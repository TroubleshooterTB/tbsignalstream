"use client";

import React, { useState, useTransition } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCatalystScore } from "@/app/actions";
import { BrainCircuit, Loader2, Sparkles } from "lucide-react";
import { Progress } from "./ui/progress";

const formSchema = z.object({
  ticker: z.string().min(1, "Ticker is required.").toUpperCase(),
  newsArticles: z.string().min(10, "At least one news article URL is required."),
});

type CatalystResult = {
  summary: string;
  catalystScore: number;
};

export function CatalystEngine() {
  const [isPending, startTransition] = useTransition();
  const [result, setResult] = useState<CatalystResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      ticker: "",
      newsArticles: "",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    setError(null);
    setResult(null);
    startTransition(async () => {
      const response = await getCatalystScore(values);
      if (response.error) {
        setError(typeof response.error === 'string' ? response.error : "Invalid input. Please check the fields.");
      } else if (response.data) {
        setResult(response.data as CatalystResult);
      }
    });
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="text-center">
        <h1 className="text-3xl font-bold tracking-tight">AI News Catalyst Engine</h1>
        <p className="text-muted-foreground">
          Summarize news and get a catalyst score with GenAI.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>Analyze Stock News</CardTitle>
          <CardDescription>Enter a stock ticker and related news article URLs.</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="ticker"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Stock Ticker (e.g., RELIANCE)</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter ticker symbol" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="newsArticles"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>News Article URLs</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Enter each URL on a new line"
                        className="min-h-[120px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Provide links to news articles for analysis.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" disabled={isPending}>
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <BrainCircuit className="mr-2 h-4 w-4" />
                    Get Catalyst Score
                  </>
                )}
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>

      {isPending && (
        <Card>
          <CardContent className="pt-6 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
            <p className="text-muted-foreground">Our AI is analyzing the news... this may take a moment.</p>
          </CardContent>
        </Card>
      )}

      {error && <p className="text-destructive text-center">{error}</p>}

      {result && (
        <Card className="bg-gradient-to-br from-primary/5 to-accent/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
                <Sparkles className="text-accent" />
                AI Analysis Complete
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
              <div>
                  <h3 className="text-lg font-semibold mb-2">Catalyst Score</h3>
                  <div className="flex items-center gap-4">
                    <span className="text-4xl font-bold text-primary">
                      {(result.catalystScore * 100).toFixed(0)}
                      <span className="text-2xl text-muted-foreground">/100</span>
                    </span>
                    <Progress value={result.catalystScore * 100} className="flex-1 h-3" />
                  </div>
                   <p className="text-xs text-muted-foreground mt-1">
                      Score indicates potential market impact (0=Negative, 50=Neutral, 100=Positive).
                  </p>
              </div>
              <div>
                  <h3 className="text-lg font-semibold mb-2">News Summary</h3>
                  <p className="text-muted-foreground leading-relaxed">{result.summary}</p>
              </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
