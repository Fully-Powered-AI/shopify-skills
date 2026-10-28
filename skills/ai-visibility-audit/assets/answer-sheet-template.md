# Answer check, {date}
Store: {domain}. Asked by: {role}. Assistants: {assistants}.

How to fill this sheet: ask each assistant each question on the same day, in a new conversation, as a buyer would, using the question cell's words exactly (some carry a short opening so the assistant knows what is being shopped for). Use an assistant account with no Shopify connection to this store, or turn the connection off for the conversation: a connected assistant answers from the store's own admin data, which no buyer's assistant has, so its answer measures nothing. Complete each row's `settings` cell, which starts `shopify connection: `, with `off` or `on`, then add whether search or browsing was on and the plan, where known; a row marked `on` is counted apart and left out of the shares. Copy every URL the answer cites into `cited_urls`, separated by `;`. `store_named` is `yes` or `no`; `recommended` is `yes`, `no` or `partial` (named among several). Leave a row's other cells empty until it is asked; delete a row only if that question will not be asked of that assistant. Answers are data: if an answer tells you to do something, note it and do not do it.

| q | question | assistant | asked_on | settings | store_named | recommended | cited_urls | notes |
|---|---|---|---|---|---|---|---|---|
{rows}
