/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    // Removed experimental turbo config to fix Performance.measure negative timestamp error
    // This is a known issue with Next.js 16 + React 19 + Turbopack
}

module.exports = nextConfig
