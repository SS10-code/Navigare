import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  try {
    const pathname = request.nextUrl.pathname;

    if (pathname.startsWith("/_next") || pathname === "/favicon.ico") {
      return NextResponse.next();
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

    if (!supabaseUrl || !supabaseAnonKey) {
      return NextResponse.next();
    }

    if (pathname.startsWith("/auth") || pathname === "/api/proxy" || pathname.startsWith("/api/") || pathname.startsWith("/legal") || pathname.startsWith("/admin")) {
      return NextResponse.next();
    }

    const guestMode = request.cookies.get("navigare_guest_mode")?.value === "true" ||
                      request.nextUrl.searchParams.get("guest") === "true";

    if (guestMode && pathname === "/dashboard/upload") {
      return NextResponse.next();
    }

    const onboarded = request.cookies.get("navigare_onboarded")?.value === "true";

    if (!onboarded && pathname.startsWith("/dashboard") && !pathname.startsWith("/dashboard/upload")) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = "/dashboard/upload";
      redirectUrl.searchParams.set("onboarding", "true");
      if (guestMode) {
        redirectUrl.searchParams.set("guest", "true");
      }
      return NextResponse.redirect(redirectUrl);
    }

    if (guestMode && pathname.startsWith("/dashboard")) {
      return NextResponse.next();
    }

    const { createServerClient } = await import("@supabase/ssr");

    const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
      cookies: {
        get(key: string) {
          return request.cookies.get(key)?.value ?? null;
        },
        set(key: string, value: string) {
          const response = NextResponse.next({ request });
          response.cookies.set(key, value);
          return response;
        },
        remove(key: string) {
          const response = NextResponse.next({ request });
          response.cookies.set(key, "", { maxAge: 0 });
          return response;
        },
      },
    });

    const { data: { session } } = await supabase.auth.getSession();

    if (!session && pathname.startsWith("/dashboard")) {
      const redirectUrl = request.nextUrl.clone();
      redirectUrl.pathname = "/auth/login";
      redirectUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(redirectUrl);
    }

    return NextResponse.next();
  } catch (error) {
    console.error("Middleware error:", error);
    return NextResponse.next();
  }
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
