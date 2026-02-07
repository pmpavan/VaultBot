import { assertEquals, assertExists } from "https://deno.land/std@0.192.0/testing/asserts.ts";
import { createClient } from "@supabase/supabase-js";
// Import the actual function to test
import { logToDLQ } from "./index.ts";

/**
 * Integration test for DLQ functionality
 * Tests the complete flow of error capture and DLQ insertion
 * 
 * NOTE: This test requires a running Supabase instance with the dlq_jobs table
 * Run with: deno test --allow-env --allow-net --allow-read test_dlq_integration.ts
 */

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "http://127.0.0.1:54321";
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

Deno.test({
    name: "DLQ Integration: Insert and retrieve error from DLQ",
    ignore: !SUPABASE_SERVICE_ROLE_KEY, // Skip if no credentials
    sanitizeResources: false,
    sanitizeOps: false,
    fn: async () => {
        const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY!, {
            auth: { persistSession: false }
        });

        const testPayload = {
            From: "whatsapp:+1234567890",
            Body: "Integration test message",
            MessageSid: "SM_INTEGRATION_TEST",
            ProfileName: "Test User"
        };

        const testError = new Error("Integration test database error");
        const testContext = {
            userPhone: "+1234567890",
            sourceType: "dm",
            sourceChannelId: "+1234567890"
        };

        // Use the actual function to insert into DLQ
        const success = await logToDLQ(supabase, testPayload, testError, testContext);

        assertEquals(success, true, "DLQ insertion should succeed");

        // Verify we can query the DLQ entry - find the one we just inserted
        // We'll search by the unique MessageSid in the payload to find ours
        const { data: queryData, error: queryError } = await supabase
            .from('dlq_jobs')
            .select('*')
            .eq('original_payload->>MessageSid', testPayload.MessageSid)
            .order('created_at', { ascending: false })
            .limit(1)
            .single();

        assertEquals(queryError, null, "DLQ query should succeed");
        assertExists(queryData, "DLQ entry should be retrievable");
        assertEquals(queryData.error_message, testError.message);
        assertEquals(queryData.error_type, testError.name);
        assertEquals(queryData.user_phone, testContext.userPhone);

        // Cleanup: Delete test entry
        await supabase
            .from('dlq_jobs')
            .delete()
            .eq('id', queryData.id);

        console.log("✅ DLQ integration test passed");
    }
});

Deno.test({
    name: "DLQ Integration: Simulate database insert failure",
    ignore: !SUPABASE_SERVICE_ROLE_KEY,
    sanitizeResources: false,
    sanitizeOps: false,
    fn: async () => {
        const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY!, {
            auth: { persistSession: false }
        });

        const testPayload = {
            From: "whatsapp:+9999999999",
            Body: "Simulated failure test"
        };

        // Simulate a job insertion failure by trying to insert with invalid data
        const { data: jobData, error: jobError } = await supabase
            .from('jobs')
            .insert({
                source_channel_id: "test-channel",
                source_type: "invalid_type",  // This should fail CHECK constraint
                user_id: "+9999999999", // User doesn't exist, might also fail FK if strict
                payload: testPayload,
                status: 'pending'
            })
            .select()
            .single();

        // Job insertion should fail
        assertExists(jobError, "Job insertion should fail with invalid source_type");

        // Now log this failure to DLQ using real function
        const success = await logToDLQ(supabase, testPayload, jobError, {
            userPhone: "+9999999999",
            sourceType: "invalid_type",
            sourceChannelId: "test-channel"
        });

        assertEquals(success, true, "DLQ insertion should succeed even when job fails");

        // Give it a moment to index/propagate
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Verify entry exists - key off unique user_phone
        const { data: dlqData, error: dlqError } = await supabase
            .from('dlq_jobs')
            .select('*')
            .eq('user_phone', '+9999999999')
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();

        assertEquals(dlqError, null);
        assertExists(dlqData, "DLQ entry should be created");

        // Note: Error details from Postgres might vary slightly in format (e.g. object vs string)
        // so we check if error_message is populated rather than strict equality
        assertExists(dlqData.error_message);

        // Verify user phone captured
        assertEquals(dlqData.user_phone, "+9999999999");

        // Cleanup
        if (dlqData) {
            await supabase
                .from('dlq_jobs')
                .delete()
                .eq('id', dlqData.id);
        }

        console.log("✅ DLQ failure simulation test passed");
    }
});

Deno.test({
    name: "DLQ Integration: Query DLQ by user phone",
    ignore: !SUPABASE_SERVICE_ROLE_KEY,
    sanitizeResources: false,
    sanitizeOps: false,
    fn: async () => {
        const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY!, {
            auth: { persistSession: false }
        });

        const testUserPhone = "+1111111111";
        const testPayload = {
            From: `whatsapp:${testUserPhone}`,
            Body: "Query test"
        };

        // Insert multiple DLQ entries for the same user using real function
        await logToDLQ(supabase, testPayload, new Error("Error 1"), { userPhone: testUserPhone });
        await logToDLQ(supabase, testPayload, new Error("Error 2"), { userPhone: testUserPhone });

        // Query DLQ by user phone
        const { data: userErrors, error: queryError } = await supabase
            .from('dlq_jobs')
            .select('*')
            .eq('user_phone', testUserPhone)
            .order('created_at', { ascending: false });

        assertEquals(queryError, null, "Query should succeed");
        assertExists(userErrors, "Should return user errors");
        assertEquals(userErrors.length >= 2, true, "Should find at least 2 errors");

        // Cleanup
        const idsToDelete = userErrors.map(e => e.id);
        await supabase
            .from('dlq_jobs')
            .delete()
            .in('id', idsToDelete);

        console.log("✅ DLQ query by user test passed");
    }
});

console.log("✅ All DLQ integration tests completed");
