import { test, expect } from '@playwright/test';

test('debug sidebar shows rag telemetry and topk expansion', async ({ page }) => {
  await page.goto('http://localhost:3000');
  // mount admin UI if needed
  // ensure debug data is present by mocking the /api/chat endpoint response
  await page.route('**/api/chat', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        reply: 'Found it in doc',
        user_id: 'u1',
        session_id: 's1',
        history: [],
        debug: {
          request_json: {},
          user_id: 'u1',
          session_id: 's1',
          user_query: 'Where is X?',
          rag_context: [],
          rag_telemetry: {
            run_id: 'r1',
            decision: 'hit',
            elapsed_s: 0.02,
            latency_embed_s: 0.001,
            latency_retrieval_s: 0.01,
            config_snapshot: { k: 5, threshold: 0.2 },
            topk: [{ id: 'doc1:0', document: 'This is chunk content', metadata: { title: 'Doc1' }, score_vector: 0.9, score_sparse: 0.2, score_final: 0.85 }]
          },
          final_llm_prompt: 'PROMPT'
        }
      })
    });
  });

  await page.fill('textarea[placeholder="Type a message"]', 'Where is X?');
  await page.click('button:has-text("Send")');

  await expect(page.locator('text=Run ID: r1')).toBeVisible();
  await expect(page.locator('text=Doc1')).toBeVisible();

  // click topk row to expand
  await page.click('tbody tr:first-child');
  await expect(page.locator('pre').first()).toContainText('This is chunk content');
});