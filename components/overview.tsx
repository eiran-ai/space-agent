import { motion } from "framer-motion";
import Link from "next/link";

import { BrainIcon, Satellite } from "lucide-react";

export const Overview = () => {
  return (
    <motion.div
      key="overview"
      className="max-w-3xl mx-auto md:mt-16"
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.98 }}
      transition={{ delay: 0.2 }}
    >
      <div className="rounded-xl p-6 flex flex-col gap-4 leading-relaxed text-center max-w-xl">
        <p className="flex flex-row justify-center gap-4 items-center">
          <Satellite/>
          <span>+</span>
          <BrainIcon/>
        </p>

        <h1 className="text-xl font-semibold">Space Agent</h1>
        <p className="text-sm text-muted-foreground">
          A smart assistant for satellite imagery. It detects objects and compares
          areas over time using geo-metadata to reveal meaningful change.
        </p>

        <div className="text-left text-sm mx-auto">
          <div className="font-medium mb-1">What you can do</div>
          <ul className="list-disc list-outside ml-5 space-y-1">
            <li>Detect roads, buildings, ships, farms, and more.</li>
            <li>Compare current vs. past imagery to spot expansion or loss.</li>
            <li>Ask simple questions; get plain-language answers.</li>
          </ul>
        </div>

        <div className="text-left text-sm mx-auto">
          <div className="font-medium mb-1">Ideas to try</div>
          <ul className="list-disc list-outside ml-5 space-y-1">
            <li>&quot;What stands out in this port image?&quot;</li>
            <li>&quot;Summarize detected objects and likely activity.&quot;</li>
            <li>&quot;Compare this area to earlier images and describe changes.&quot;</li>
          </ul>
        </div>

        {/* <p className="text-xs text-muted-foreground">
          Built by Eiran
        </p> */}
      </div>
    </motion.div>
  );
};
