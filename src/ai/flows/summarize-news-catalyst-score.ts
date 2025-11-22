'use server';
/**
 * @fileOverview Summarizes news articles for a given stock and assigns a catalyst score.
 *
 * - summarizeNewsAndGetCatalystScore - A function that handles the summarization and scoring process.
 * - SummarizeNewsCatalystScoreInput - The input type for the summarizeNewsAndGetCatalystScore function.
 * - SummarizeNewsCatalystScoreOutput - The return type for the summarizeNewsAndGetCatalystScore function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const SummarizeNewsCatalystScoreInputSchema = z.object({
  ticker: z.string().describe('The ticker symbol of the stock.'),
  newsArticles: z.array(z.string()).describe('An array of news article URLs.'),
});
export type SummarizeNewsCatalystScoreInput = z.infer<typeof SummarizeNewsCatalystScoreInputSchema>;

const SummarizeNewsCatalystScoreOutputSchema = z.object({
  summary: z.string().describe('A summary of the news articles.'),
  catalystScore: z.number().describe('A score between 0 and 1 indicating the potential impact of the news on the stock price.'),
});
export type SummarizeNewsCatalystScoreOutput = z.infer<typeof SummarizeNewsCatalystScoreOutputSchema>;

export async function summarizeNewsAndGetCatalystScore(input: SummarizeNewsCatalystScoreInput): Promise<SummarizeNewsCatalystScoreOutput> {
  return summarizeNewsCatalystScoreFlow(input);
}

const summarizeNewsPrompt = ai.definePrompt({
  name: 'summarizeNewsPrompt',
  input: {schema: SummarizeNewsCatalystScoreInputSchema},
  output: {schema: SummarizeNewsCatalystScoreOutputSchema},
  prompt: `You are an AI assistant that summarizes news articles for a given stock and assigns a catalyst score.

  Instructions:
  1. Summarize the provided news articles for the stock ticker: {{{ticker}}}.
  2. Analyze the sentiment of the news and assign a catalyst score between 0 and 1 based on the potential impact on the stock price.
     - 0 indicates a negative catalyst, meaning the news is likely to have a negative impact on the stock price.
     - 1 indicates a positive catalyst, meaning the news is likely to have a positive impact on the stock price.
     - 0.5 indicates a neutral catalyst, meaning the news is unlikely to have a significant impact on the stock price.

  News Articles:
  {{#each newsArticles}}
  - {{{this}}}
  {{/each}}

  Summary and Catalyst Score:`,
});

const summarizeNewsCatalystScoreFlow = ai.defineFlow(
  {
    name: 'summarizeNewsCatalystScoreFlow',
    inputSchema: SummarizeNewsCatalystScoreInputSchema,
    outputSchema: SummarizeNewsCatalystScoreOutputSchema,
  },
  async input => {
    const {output} = await summarizeNewsPrompt(input);
    return output!;
  }
);
