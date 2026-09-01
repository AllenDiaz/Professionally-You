import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal .next/standalone build (only the files needed to run)
  // for a lean container image — see frontend/Containerfile.
  output: "standalone",
};

export default nextConfig;
