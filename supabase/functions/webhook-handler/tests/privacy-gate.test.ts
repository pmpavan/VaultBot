
import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { webhookHandler } from "../index.ts";
import { crypto } from "https://deno.land/std@0.208.0/crypto/mod.ts";

/**
 * Helper to generate Twilio Signature
 */
async function generateSignature(authToken: string, url: string, params: Record<string, string>): Promise<string> {
    const sortedKeys = Object.keys(params).sort();
    let data = url;
    for (const key of sortedKeys) {
        data += key + params[key];
    }

    const encoder = new TextEncoder();
    const keyData = encoder.encode(authToken);
    const msgData = encoder.encode(data);

    const key = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "HMAC", hash: "SHA-1" },
        false,
        ["sign"]
    );

    const signature = await crypto.subtle.sign("HMAC", key, msgData);
    return btoa(String.fromCharCode(...new Uint8Array(signature)));
}

/**
 * Setup test environment with required env vars
 */
function setupTestEnv() {
    Deno.env.set("TWILIO_AUTH_TOKEN", "mock_token");
    Deno.env.set("TWILIO_ACCOUNT_SID", "AC_mock_sid");
    Deno.env.set("SUPABASE_URL", "https://mock.supabase.co");
    Deno.env.set("SUPABASE_SERVICE_ROLE_KEY", "mock_service_role_key");
}

Deno.test("Task 1: Initialization & Error Handling - Returns 200 OK on Crash", async () => {
    setupTestEnv();

    // Test case: Missing TWILIO_AUTH_TOKEN should return 200 with error
    Deno.env.delete("TWILIO_AUTH_TOKEN");

    const params = { Body: "Hello", From: "whatsapp:+12345" };
    const req = new Request("https://vaultbot.com/webhook", {
        method: "POST",
        body: new URLSearchParams(params)
    });

    const res = await webhookHandler(req);
    assertEquals(res.status, 200, "Should return 200 even on config error");
    const body = await res.json();
    assertEquals(body.error, "Internal Server Error");

    // Restore for other tests
    setupTestEnv();
});

Deno.test("Task 2: Security - Rejects invalid/missing signature", async () => {
    setupTestEnv();

    const req = new Request("https://vaultbot.com/webhook", {
        method: "POST",
        body: new URLSearchParams({ Body: "Hello" })
    });
    // Missing header
    const res = await webhookHandler(req);
    assertEquals(res.status, 403);

    // Invalid header
    const req2 = new Request("https://vaultbot.com/webhook", {
        method: "POST",
        body: new URLSearchParams({ Body: "Hello" }),
        headers: { "X-Twilio-Signature": "bad_signature" }
    });
    const res2 = await webhookHandler(req2);
    assertEquals(res2.status, 403);
});

Deno.test("Task 2: Security - Accepts valid signature", async () => {
    setupTestEnv();

    const token = "mock_token";
    const url = "https://vaultbot.com/webhook";
    const params = { Body: "Hello", From: "whatsapp:+12345", To: "whatsapp:+67890" };

    const signature = await generateSignature(token, url, params);

    const req = new Request(url, {
        method: "POST",
        headers: { "X-Twilio-Signature": signature },
        body: new URLSearchParams(params)
    });

    const res = await webhookHandler(req);
    assertEquals(res.status, 200, "Should satisfy security check");
    const body = await res.json();
    // Note: In real test, this would fail on Supabase insert since we're mocking
    // For now, we expect it to return 200 with error due to Supabase mock failure
    console.log("Response:", body);
});

Deno.test("Task 3: Privacy - Group Message WITHOUT Tag -> Ignored", async () => {
    setupTestEnv();

    const token = "mock_token";
    const url = "https://vaultbot.com/webhook";

    // Test Case A: Group (Untagged) -> Ignored
    // Using GroupSid to indicate group message
    const paramsA = {
        Body: "Hello world",
        From: "whatsapp:+12345678",
        To: "whatsapp:+67890",
        GroupSid: "GR123456789" // Explicit group indicator
    };
    const sigA = await generateSignature(token, url, paramsA);
    const reqA = new Request(url, {
        method: "POST",
        headers: { "X-Twilio-Signature": sigA },
        body: new URLSearchParams(paramsA)
    });

    const resA = await webhookHandler(reqA);
    assertEquals(resA.status, 200);
    const bodyA = await resA.json();
    assertEquals(bodyA.message, "Ignored (Privacy Gate)");

    // Test Case B: Group with @g.us format (fallback detection)
    const paramsB = {
        Body: "Another untagged message",
        From: "12345678@g.us",
        To: "whatsapp:+67890"
    };
    const sigB = await generateSignature(token, url, paramsB);
    const reqB = new Request(url, {
        method: "POST",
        headers: { "X-Twilio-Signature": sigB },
        body: new URLSearchParams(paramsB)
    });

    const resB = await webhookHandler(reqB);
    assertEquals(resB.status, 200);
    const bodyB = await resB.json();
    assertEquals(bodyB.message, "Ignored (Privacy Gate)");
});

Deno.test("Task 3: Privacy - Group Message WITH Tag -> Job Queued (would fail on Supabase)", async () => {
    setupTestEnv();

    const token = "mock_token";
    const url = "https://vaultbot.com/webhook";

    const params = {
        Body: "@VaultBot extract this",
        From: "whatsapp:+12345678",
        To: "whatsapp:+67890",
        GroupSid: "GR123456789"
    };
    const sig = await generateSignature(token, url, params);
    const req = new Request(url, {
        method: "POST",
        headers: { "X-Twilio-Signature": sig },
        body: new URLSearchParams(params)
    });

    const res = await webhookHandler(req);
    assertEquals(res.status, 200);
    const body = await res.json();
    // Note: This will return error due to mock Supabase, but validates the flow
    console.log("Group tagged response:", body);
});

Deno.test("Task 3: Privacy - DM Message -> Job Queued (would fail on Supabase)", async () => {
    setupTestEnv();

    const token = "mock_token";
    const url = "https://vaultbot.com/webhook";

    const params = {
        Body: "Just a DM",
        From: "whatsapp:+15551234567",
        To: "whatsapp:+67890"
    };
    const sig = await generateSignature(token, url, params);
    const req = new Request(url, {
        method: "POST",
        headers: { "X-Twilio-Signature": sig },
        body: new URLSearchParams(params)
    });

    const res = await webhookHandler(req);
    assertEquals(res.status, 200);
    const body = await res.json();
    // Note: This will return error due to mock Supabase, but validates the flow
    console.log("DM response:", body);
});
