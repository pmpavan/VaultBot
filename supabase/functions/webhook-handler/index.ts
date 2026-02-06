import { createClient } from "@supabase/supabase-js";
import twilio from "twilio";

// Twilio helper exports
const { validateRequest } = twilio;

console.log("Hello from Functions!");

export const webhookHandler = async (req: Request): Promise<Response> => {
    try {
        const url = req.url;
        const params = await req.formData();

        // Convert FormData to Record<string, any>
        const body: Record<string, any> = {};
        params.forEach((value, key) => {
            body[key] = value;
        });

        const signature = req.headers.get("X-Twilio-Signature");
        const authToken = Deno.env.get("TWILIO_AUTH_TOKEN");
        const accountSid = Deno.env.get("TWILIO_ACCOUNT_SID") || "AC_mock_sid";

        if (!authToken) {
            console.error("CRITICAL: Missing TWILIO_AUTH_TOKEN");
            throw new Error("Missing TWILIO_AUTH_TOKEN");
        }

        // 1. Validate Request
        let isValid = false;
        try {
            isValid = validateRequest(authToken, signature || "", url, body);
        } catch (e) {
            console.error("Validation threw error:", e);
            isValid = false;
        }

        if (!isValid) {
            console.warn("Invalid Twilio Signature");
            return new Response(JSON.stringify({ error: "Forbidden" }), {
                status: 403,
                headers: { "Content-Type": "application/json" }
            });
        }

        // 2. Parse Source Type & Privacy Gate
        const from = body["From"] || "";
        const to = body["To"] || "";
        const messageBody = body["Body"] || "";
        const messageSid = body["MessageSid"] || "";

        console.log(`Received message from ${from}: ${messageBody.substring(0, 50)}... [SID: ${messageSid}]`);

        // Extract user phone (remove whatsapp: prefix if present)
        const userPhone = from.replace(/^whatsapp:/, "");

        // Detect Source Type
        // For Twilio WhatsApp, group messages have specific indicators:
        // - Check for GroupSid in the payload (if available)
        // - Check if From contains group-like patterns
        // - For now, use a more robust heuristic: check if message has group metadata
        let sourceType = 'dm';
        const groupSid = body["GroupSid"] || "";

        // Improved group detection:
        // 1. Check for explicit GroupSid field (Twilio may provide this)
        // 2. Check for @g.us pattern in From field (WhatsApp group JID format)
        // 3. Default to DM if uncertain (safer for privacy)
        if (groupSid || from.includes("@g.us")) {
            sourceType = 'group';
        }

        // Extract source_channel_id (the chat/group identifier)
        // For groups: use GroupSid if available, otherwise extract from From
        // For DMs: use the user's phone number
        let sourceChannelId = sourceType === 'group'
            ? (groupSid || from.replace(/^whatsapp:/, ""))
            : userPhone;

        const isTagged = messageBody.includes("@VaultBot") || body["ReferralNumMedia"] === "1";

        // Privacy Gate: If group AND not tagged -> Return 200 (No-Op)
        if (sourceType === 'group' && !isTagged) {
            console.log("Privacy Gate: Group message not tagged. Ignoring.");
            return new Response(JSON.stringify({ message: "Ignored (Privacy Gate)" }), {
                status: 200,
                headers: { "Content-Type": "application/json" }
            });
        }

        // 3. Job Insertion - REAL IMPLEMENTATION
        const supabaseUrl = Deno.env.get("SUPABASE_URL");
        const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

        if (!supabaseUrl || !supabaseKey) {
            console.error("CRITICAL: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
            throw new Error("Missing Supabase configuration");
        }

        const supabase = createClient(supabaseUrl, supabaseKey, {
            auth: { persistSession: false }
        });

        console.log(`Inserting Job: [${sourceType}] from ${userPhone} in channel ${sourceChannelId}`);

        const { data: jobData, error: jobError } = await supabase
            .from('jobs')
            .insert({
                source_channel_id: sourceChannelId,
                source_type: sourceType,
                user_phone: userPhone,
                payload: body,
                status: 'pending'
            })
            .select()
            .single();

        if (jobError) {
            console.error("Failed to insert job:", jobError);
            throw new Error(`Database insert failed: ${jobError.message}`);
        }

        console.log(`Job created successfully: ${jobData.id}`);

        // 4. User Reaction
        try {
            if (accountSid && authToken && !authToken.includes("mock")) {
                const client = twilio(accountSid, authToken);
                await client.messages.create({
                    from: to,
                    to: from,
                    body: '📝'
                });
                console.log("Reaction sent successfully.");
            } else {
                console.log("Skipping reaction (Mock/Test Env)");
            }
        } catch (reactionError) {
            // Log with more context for debugging
            console.error("Failed to send reaction:", {
                error: reactionError,
                from: from,
                to: to,
                messageSid: messageSid
            });
            // Non-blocking - continue even if reaction fails
        }

        return new Response(
            JSON.stringify({ message: "Job Queued", jobId: jobData.id }),
            { headers: { "Content-Type": "application/json" } },
        );

    } catch (error) {
        console.error("CRITICAL ERROR in webhook-handler:", error);
        return new Response(
            JSON.stringify({ error: "Internal Server Error", details: String(error) }),
            {
                status: 200,
                headers: { "Content-Type": "application/json" }
            },
        );
    }
}

// Supabase Edge Functions are always served
Deno.serve(webhookHandler);
