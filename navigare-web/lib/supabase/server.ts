import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(key: string) {
          return cookieStore.get(key)?.value;
        },
        set(key: string, value: string, options: CookieOptions) {
          cookieStore.set(key, value, options);
        },
        remove(key: string, options: CookieOptions) {
          cookieStore.set(key, "", { ...options, maxAge: 0 });
        },
      },
    }
  );
}
