"use server";

import { summarizeNewsAndGetCatalystScore, SummarizeNewsCatalystScoreInput, SummarizeNewsCatalystScoreOutput } from '@/ai/flows/summarize-news-catalyst-score';
import { z } from 'zod';

const formSchema = z.object({
  ticker: z.string().min(1, "Ticker is required."),
  newsArticles: z.string().min(10, "At least one news article URL is required."),
});

type ActionResponse = {
    data?: SummarizeNewsCatalystScoreOutput;
    error?: string | z.ZodFormattedError<z.infer<typeof formSchema>>;
}

export async function getCatalystScore(values: z.infer<typeof formSchema>): Promise<ActionResponse> {
  const parsed = formSchema.safeParse(values);
  if (!parsed.success) {
    return { error: parsed.error.format() };
  }
  
  const newsUrls = parsed.data.newsArticles
    .split('\n')
    .map(url => url.trim())
    .filter(url => url.startsWith('http'));

  if(newsUrls.length === 0) {
    return { error: "Please provide valid URLs." };
  }

  const input: SummarizeNewsCatalystScoreInput = {
    ticker: parsed.data.ticker,
    newsArticles: newsUrls,
  };

  try {
    const result = await summarizeNewsAndGetCatalystScore(input);
    return { data: result };
  } catch (e) {
    console.error(e);
    return { error: 'An unexpected error occurred while processing your request.' };
  }
}
