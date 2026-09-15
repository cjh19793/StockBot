import Hero from "@/components/landing/Hero";
import FeatureGrid from "@/components/landing/FeatureGrid";
import HowItWorks from "@/components/landing/HowItWorks";
import FinalCta from "@/components/landing/FinalCta";

export default function HomePage() {
  return (
    <div>
      <Hero />
      <FeatureGrid />
      <HowItWorks />
      <FinalCta />
    </div>
  );
}
