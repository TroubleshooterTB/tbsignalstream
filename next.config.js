/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  outputFileTracingRoot: require('path').join(__dirname, '../'),
  staticPageGenerationTimeout: 120,
  swcMinify: true,
  productionBrowserSourceMaps: false,
  typescript: {
    // Skip type checking during build if SKIP_TYPE_CHECK is set
    ignoreBuildErrors: process.env.SKIP_TYPE_CHECK === 'true',
  },
  eslint: {
    // Skip ESLint during build
    ignoreDuringBuilds: true,
  },
  env: {
    NEXT_PUBLIC_FIREBASE_WEBAPP_CONFIG: JSON.stringify(process.env.FIREBASE_WEBAPP_CONFIG),
  },
};

module.exports = nextConfig;
