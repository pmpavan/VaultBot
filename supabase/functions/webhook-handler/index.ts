import { createClient } from "@supabase/supabase-js";
import twilio from "twilio";

// Twilio helper exports
const { validateRequest } = twilio;

console.log("Hello from Functions!");

/**
 * Get or create a user profile based on phone number.
 * If user exists, returns existing user_id.
 * If user doesn't exist, creates new user with ProfileName as first_name.
 * 
 * @param supabase - Supabase client instance
 * @param phoneNumber - User's phone number (primary key)
 * @param profileName - WhatsApp profile name (defaults to "Unknown")
 * @returns phone_number (which is the user_id/PK)
 */
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
        .maybeSingle();  // Use maybeSingle to avoid error on no results

    if (selectError) {
        console.error("Error checking for existing user:", selectError);
        throw new Error(`User lookup failed: ${selectError.message}`);
    }

    if (existingUser) {
        console.log(`Existing user found: ${phoneNumber}`);
        return phoneNumber;
    }

    // 2. Create new user
    const firstName = profileName || 'Unknown';
    console.log(`Creating new user: ${phoneNumber} (${firstName})`);

    const { data: newUser, error: insertError } = await supabase
        .from('users')
        .insert({
            phone_number: phoneNumber,
            first_name: firstName
        })
        .select('phone_number')
        .single();

    if (insertError) {
        // Handle race condition: if another request created the user simultaneously
        if (insertError.code === '23505') {  // Unique violation
            console.log(`User ${phoneNumber} was created by concurrent request`);
            return phoneNumber;
        }
        console.error("Error creating user:", insertError);
        throw new Error(`User creation failed: ${insertError.message}`);
    }

    console.log(`New user created: ${newUser.phone_number}`);
    return newUser.phone_number;

}

/**
 * Log failed webhook processing to Dead Letter Queue (DLQ).
 * Captures original payload and error context for debugging.
 * Fails gracefully - never throws errors to prevent blocking webhook response.
 * 
 * @param supabase - Supabase client instance
 * @param originalPayload - Complete webhook payload that failed processing
 * @param error - Error object or unknown error
 * @param context - Optional context (userPhone, sourceType, sourceChannelId)
 * @returns boolean indicating success/failure of DLQ insertion
 */
export async function logToDLQ(
    supabase: any,
    originalPayload: Record<string, any>,
    error: Error | unknown,
    context: {
        userPhone?: string;
        sourceType?: string;
        sourceChannelId?: string;
    } = {}
): Promise<boolean> {
    try {
        // Extract error details
        const errorMessage = error instanceof Error ? error.message : String(error);
        const errorType = error instanceof Error ? error.name : 'UnknownError';

        console.log(`Logging to DLQ: ${errorType} - ${errorMessage}`);

        // Insert into DLQ table
        const { error: dlqError } = await supabase
            .from('dlq_jobs')
            .insert({
                original_payload: originalPayload,
                error_message: errorMessage,
                error_type: errorType,
                user_phone: context.userPhone,
                source_type: context.sourceType,
                source_channel_id: context.sourceChannelId
            });

        if (dlqError) {
            console.error('Failed to insert into DLQ:', dlqError);
            return false;
        }

        console.log('Successfully logged error to DLQ');
        return true;
    } catch (dlqException) {
        // DLQ insertion failed - log but don't throw
        // This ensures we never block the webhook response
        console.error('CRITICAL: DLQ insertion failed:', dlqException);
        return false;
    }
}


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

        // 3.5. Get or Create User Profile
        const profileName = body["ProfileName"] || "Unknown";
        let userId: string;
        try {
            userId = await getOrCreateUser(supabase, userPhone, profileName);
            console.log(`User resolved: ${userId} (${profileName})`);
        } catch (userError) {
            console.error("User creation/lookup failed:", userError);
            // Log to DLQ before re-throwing
            await logToDLQ(supabase, body, userError, {
                userPhone,
                sourceType,
                sourceChannelId
            });
            throw userError;  // Re-throw to be caught by main catch block
        }


        const { data: jobData, error: jobError } = await supabase
            .from('jobs')
            .insert({
                source_channel_id: sourceChannelId,
                source_type: sourceType,
                user_id: userId,  // Add user_id FK
                payload: body,
                status: 'pending'
            })
            .select()
            .single();

        if (jobError) {
            console.error("Failed to insert job:", jobError);
            // Log to DLQ before throwing
            await logToDLQ(supabase, body, jobError, {
                userPhone,
                sourceType,
                sourceChannelId
            });
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

        // Only log to DLQ if standard processing didn't already handle it
        // We check if the error was re-thrown from a known catch block that already logged to DLQ
        // However, since we can't easily check that, we'll try to extract context from variables in scope
        // BUT crucial fix: we cannot re-read req.formData() as it's already consumed.

        try {
            // Get Supabase client if not already initialized
            const supabaseUrl = Deno.env.get("SUPABASE_URL");
            const supabaseKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");

            if (supabaseUrl && supabaseKey) {
                const supabase = createClient(supabaseUrl, supabaseKey, {
                    auth: { persistSession: false }
                });

                // Attempt to reconstruct context from variables in scope if available
                // We rely on 'body' variable being available in closure if defined, 
                // but since variables declared in try block aren't available here, we need a safer approach.
                // In this specific handler structure, meaningful variables are inside the try block.
                // We can't access 'body', 'userPhone' etc. here safely if they weren't defined.

                // For a global catch, we log what we can. 
                // To properly access the body in catch, we should have declared it outside try
                // or just log a generic "Request Failed" entry if we can't access parsing results.

                // IMPORTANT: We cannot re-read the body. We must proceed with minimal context.
                await logToDLQ(supabase, { raw_body: "Use Supabase Logs for Request Details (Body Consumed)" }, error, {
                    // We can't reliably access userPhone/sourceType here as they are block-scoped
                    // This is a trade-off: detailed DLQ logging happens in specific catch blocks
                    // This global catch catches unexpected crashes where context might be missing
                    userPhone: undefined,
                    sourceType: undefined,
                    sourceChannelId: undefined
                });
            } else {
                console.error("Cannot log to DLQ: Missing Supabase credentials");
            }
        } catch (dlqError) {
            // DLQ logging failed - log but continue
            console.error("Failed to log error to DLQ:", dlqError);
        }

        // ALWAYS return 200 OK to Twilio to prevent webhook retries
        return new Response(
            JSON.stringify({ error: "Internal Server Error", details: String(error) }),
            {
                status: 200,  // Critical: prevent Twilio retries
                headers: { "Content-Type": "application/json" }
            },
        );
    }
}

// Supabase Edge Functions are always served
// Only start the server if this file is the main entry point
if (import.meta.main) {
    Deno.serve(webhookHandler);
}
