/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Free-tier / CI: skip lint pass during build (types still checked)
  eslint: { ignoreDuringBuilds: true },
};

export default nextConfig;
