/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    const backend = process.env.BACKEND_ORIGIN || (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8002" : "http://127.0.0.1:8002");
    return [
      {
        source: "/api/:path*",
        destination: `${backend}/api/:path*`,
      },
      {
        source: "/static/:path*",
        destination: `${backend}/static/:path*`,
      },
      {
        source: "/docs",
        destination: `${backend}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${backend}/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;
