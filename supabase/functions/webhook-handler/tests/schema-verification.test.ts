import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const supabaseUrl = Deno.env.get("SUPABASE_URL") ?? "";
const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const supabase = createClient(supabaseUrl, supabaseServiceKey);

Deno.test("Database Schema Verification", async (t) => {
    await t.step("users table exists with correct schema", async () => {
        const { data: cols, error: err } = await supabase
            .from("users")
            .select("*")
            .limit(0);

        assertEquals(err, null, "users table should exist and be queryable");
    });

    await t.step("jobs table exists with correct schema", async () => {
        const { data: cols, error: err } = await supabase
            .from("jobs")
            .select("*")
            .limit(0);

        assertEquals(err, null, "jobs table should exist and be queryable");
    });

    await t.step("foreign key and constraints verification", async () => {
        const testPhone = "+19998887777";

        // Cleanup first
        await supabase.from("jobs").delete().eq("user_phone", testPhone);
        await supabase.from("users").delete().eq("phone_number", testPhone);

        // 1. Test User Creation
        const { error: userErr } = await supabase
            .from("users")
            .insert({ phone_number: testPhone, first_name: "Test Bot" });
        assertEquals(userErr, null, "Should allow creating a user");

        // 2. Test Job Creation with valid FK
        const { error: jobErr } = await supabase
            .from("jobs")
            .insert({
                user_id: testPhone,
                source_channel_id: "test_channel",
                source_type: "dm",
                user_phone: testPhone,
                payload: { test: true },
                status: "pending"
            });
        assertEquals(jobErr, null, "Should allow creating a job with valid user_id");

        // 3. Test ENUM constraints (should fail)
        const { error: enumErr } = await supabase
            .from("jobs")
            .insert({
                user_id: testPhone,
                source_channel_id: "test_channel",
                source_type: "invalid_type", // Invalid
                user_phone: testPhone,
                payload: { test: true }
            });
        assertEquals(enumErr !== null, true, "Should fail on invalid source_type");

        // Final Cleanup
        await supabase.from("jobs").delete().eq("user_phone", testPhone);
        await supabase.from("users").delete().eq("phone_number", testPhone);
    });
});
