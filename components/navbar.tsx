"use client";

import { Button } from "./ui/button";
import { GitIcon } from "./icons";
import { Satellite } from 'lucide-react';

import Link from "next/link";


export const Navbar = () => {
  return (
    <div className="p-2 flex flex-row gap-2 justify-between">
      <Link href="https://github.com/eiran-ai/space-agent">
        <Button variant="outline">
          <GitIcon /> View Source Code
        </Button>
      </Link>

      <Button>
        <Satellite />
        Space Agent
      </Button>
    </div>
  );
};
