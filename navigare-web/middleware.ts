import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = [
  "/login",
  "/signup",
  "/api/proxy",
  "/api",
  "/_next",
  "/favicon.ico",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some(
    (p) => pathname === p || pathname.startsWith(p + "/")
  );
}

export async function middleware(request: NextRequest) {
  try {
    const pathname = request.nextUrl.pathname;

    if (isPublicPath(pathname)) {
      return NextResponse.next();
    }

    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    const authDisabled = process.env.NEXT_PUBLIC_AUTH_DISABLED === "true";

    if (authDisabled || !supabaseUrl || !supabaseAnonKey) {
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
  matcher: ["/((?!_next/static|_next/image).*)"],
};
