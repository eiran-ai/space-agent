/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://space.abn.rw/api/:path*"
            : "/api/",
      },
      {
        source: "/static/:path*",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://space.abn.rw/static/:path*"
            : "/static/:path*",
      },
      {
        source: "/docs",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://space.abn.rw/docs"
            : "/api/docs",
      },
      {
        source: "/openapi.json",
        destination:
          process.env.NODE_ENV === "development"
            ? "https://space.abn.rw/openapi.json"
            : "/api/openapi.json",
      },
    ];
  },
};

module.exports = nextConfig;
