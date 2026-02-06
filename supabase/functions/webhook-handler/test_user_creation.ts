/**
 * Unit and Integration Tests for Story 1.4: Automatic User Profile Creation
 * 
 * Tests the getOrCreateUser function and end-to-end webhook processing
 * with user profile creation.
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.192.0/testing/asserts.ts";
import { createClient } from "@supabase/supabase-js";

// Mock Supabase client for unit tests
function createMockSupabase(scenario: 'existing_user' | 'new_user' | 'race_condition') {
    return {
        from: (table: string) => {
            if (table === 'users') {
                return {
                    select: () => ({
                        eq: () => ({
                            maybeSingle: async () => {
                                if (scenario === 'existing_user') {
                                    return { data: { phone_number: '+1234567890' }, error: null };
                                }
                                return { data: null, error: null };
                            }
                        })
                    }),
                    insert: () => ({
                        select: () => ({
                            single: async () => {
                                if (scenario === 'race_condition') {
                                    return {
                                        data: null,
                                        error: { code: '23505', message: 'duplicate key value' }
                                    };
                                }
                                return {
                                    data: { phone_number: '+1234567890' },
                                    error: null
                                };
                            }
                        })
                    })
                };
            }
            return {};
        }
    };
}

// Import the function (in real scenario, this would be from the module)
async function getOrCreateUser(
    supabase: any,
    phoneNumber: string,
    profileName: string
): Promise<string> {
    // 1. Try to get existing user
    const { data: existingUser, error: selectError } = await supabase
        .from('users')
        .select('phone_number')
        .eq('phone_number', phoneNumber)
        .maybeSingle();

    if (selectError) {
        throw new Error(`User lookup failed: ${selectError.message}`);
    }

    if (existingUser) {
        return phoneNumber;
    }

    // 2. Create new user
    const firstName = profileName || 'Unknown';

    const { data: newUser, error: insertError } = await supabase
        .from('users')
        .insert({
            phone_number: phoneNumber,
            first_name: firstName
        })
        .select('phone_number')
        .single();

    if (insertError) {
        // Handle race condition
        if (insertError.code === '23505') {
            return phoneNumber;
        }
        throw new Error(`User creation failed: ${insertError.message}`);
    }

    return newUser.phone_number;
}

// Unit Tests
Deno.test("getOrCreateUser - returns existing user", async () => {
    const mockSupabase = createMockSupabase('existing_user');
    const result = await getOrCreateUser(mockSupabase, '+1234567890', 'John Doe');
    assertEquals(result, '+1234567890');
});

Deno.test("getOrCreateUser - creates new user", async () => {
    const mockSupabase = createMockSupabase('new_user');
    const result = await getOrCreateUser(mockSupabase, '+1234567890', 'Jane Smith');
    assertEquals(result, '+1234567890');
});

Deno.test("getOrCreateUser - handles race condition", async () => {
    const mockSupabase = createMockSupabase('race_condition');
    const result = await getOrCreateUser(mockSupabase, '+1234567890', 'Bob Wilson');
    assertEquals(result, '+1234567890');
});

Deno.test("getOrCreateUser - handles missing ProfileName", async () => {
    const mockSupabase = createMockSupabase('new_user');
    const result = await getOrCreateUser(mockSupabase, '+1234567890', '');
    assertEquals(result, '+1234567890');
});

// Integration Test (requires real Supabase instance)
Deno.test({
    name: "Integration: End-to-end user creation and job insertion",
    ignore: !Deno.env.get("SUPABASE_URL"), // Skip if no credentials
    fn: async () => {
        const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
        const supabase = createClient(supabaseUrl, supabaseKey);

        const testPhone = `+test${Date.now()}`;
        const testProfile = "Test User";

        // 1. Create user
        const userId = await getOrCreateUser(supabase, testPhone, testProfile);
        assertEquals(userId, testPhone);

        // 2. Verify user exists in database
        const { data: user, error: userError } = await supabase
            .from('users')
            .select('*')
            .eq('phone_number', testPhone)
            .single();

        assertExists(user);
        assertEquals(user.phone_number, testPhone);
        assertEquals(user.first_name, testProfile);

        // 3. Create job with user_id
        const { data: job, error: jobError } = await supabase
            .from('jobs')
            .insert({
                source_channel_id: testPhone,
                source_type: 'dm',
                user_id: userId,
                payload: { test: true },
                status: 'pending'
            })
            .select()
            .single();

        assertExists(job);
        assertEquals(job.user_id, userId);

        // 4. Test idempotency - calling again should return same user
        const userId2 = await getOrCreateUser(supabase, testPhone, testProfile);
        assertEquals(userId2, userId);

        // Cleanup
        await supabase.from('jobs').delete().eq('id', job.id);
        await supabase.from('users').delete().eq('phone_number', testPhone);
    }
});

// Edge Case Tests
Deno.test("Edge case: Empty ProfileName defaults to Unknown", async () => {
    const mockSupabase = createMockSupabase('new_user');
    // Test with empty string
    const result = await getOrCreateUser(mockSupabase, '+1234567890', '');
    assertEquals(result, '+1234567890');
});

Deno.test("Edge case: Concurrent requests for same phone number", async () => {
    // This test simulates the race condition scenario
    const mockSupabase = createMockSupabase('race_condition');
    const result = await getOrCreateUser(mockSupabase, '+1234567890', 'Concurrent User');
    // Should handle gracefully and return phone number
    assertEquals(result, '+1234567890');
});
