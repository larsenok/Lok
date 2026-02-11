const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.panel');
const API = '';
const API_KEY_STORAGE_KEY = 'trialforgeOpenAIKey';
const MARKET_KEY = 'trialforgePromptLibrary';
const VOTES_KEY = 'trialforgeVoteLedger';

for (const tab of tabs) {
  tab.addEventListener('click', () => {
    tabs.forEach((t) => t.classList.remove('active'));
    panels.forEach((p) => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
}

function getStoredApiKey() {
  return localStorage.getItem(API_KEY_STORAGE_KEY) || '';
}

function authHeaders() {
  const key = getStoredApiKey();
  return key ? { 'X-OpenAI-API-Key': key } : {};
}

const apiKeyInput = document.getElementById('apiKeyInput');
const apiKeyStatus = document.getElementById('apiKeyStatus');
apiKeyInput.value = getStoredApiKey();
apiKeyStatus.textContent = apiKeyInput.value ? 'Saved locally' : 'Using server environment variable';

document.getElementById('saveApiKey').addEventListener('click', () => {
  const key = apiKeyInput.value.trim();
  if (!key) {
    apiKeyStatus.textContent = 'No key entered';
    return;
  }
  localStorage.setItem(API_KEY_STORAGE_KEY, key);
  apiKeyStatus.textContent = 'Saved locally';
});

document.getElementById('clearApiKey').addEventListener('click', () => {
  localStorage.removeItem(API_KEY_STORAGE_KEY);
  apiKeyInput.value = '';
  apiKeyStatus.textContent = 'Cleared. Using server environment variable';
});

const outputA = document.getElementById('outputA');
const outputB = document.getElementById('outputB');
const evaluationOut = document.getElementById('evaluationOut');

let lastRun = null;

function getVotes() {
  return JSON.parse(localStorage.getItem(VOTES_KEY) || '[]');
}

function setVotes(votes) {
  localStorage.setItem(VOTES_KEY, JSON.stringify(votes.slice(0, 100)));
}

function renderVotes() {
  const votes = getVotes();
  const totals = { A: 0, B: 0, Tie: 0 };
  votes.forEach((v) => {
    if (v.vote in totals) totals[v.vote] += 1;
  });

  document.getElementById('voteTotals').textContent = `Totals — A: ${totals.A} · B: ${totals.B} · Tie: ${totals.Tie}`;

  const history = document.getElementById('voteHistory');
  history.innerHTML = '';
  votes.slice(0, 8).forEach((v) => {
    const li = document.createElement('li');
    const taskSnippet = (v.task_input || '').replace(/\s+/g, ' ').slice(0, 80);
    li.textContent = `${v.vote} • ${v.timestamp} • ${taskSnippet}`;
    history.appendChild(li);
  });
}

function saveVote(vote) {
  if (!lastRun) {
    document.getElementById('voteTotals').textContent = 'Run a comparison first, then vote.';
    return;
  }

  const votes = getVotes();
  votes.unshift({
    vote,
    timestamp: new Date().toLocaleString(),
    model: lastRun.model,
    task_input: lastRun.task_input,
    strategy_a_prompt: lastRun.strategy_a_prompt,
    strategy_b_prompt: lastRun.strategy_b_prompt,
    evaluator_prompt: lastRun.evaluator_prompt,
    output_a: lastRun.output_a,
    output_b: lastRun.output_b,
    evaluation: lastRun.evaluation,
  });
  setVotes(votes);
  renderVotes();
}

document.getElementById('voteA').addEventListener('click', () => saveVote('A'));
document.getElementById('voteB').addEventListener('click', () => saveVote('B'));
document.getElementById('voteTie').addEventListener('click', () => saveVote('Tie'));

document.getElementById('runLab').addEventListener('click', async () => {
  outputA.textContent = 'Generating output A...';
  outputB.textContent = 'Generating output B...';
  evaluationOut.textContent = 'Evaluating...';

  const payload = {
    model: document.getElementById('model').value.trim(),
    task_input: document.getElementById('taskInput').value,
    strategy_a_prompt: document.getElementById('strategyAPrompt').value,
    strategy_b_prompt: document.getElementById('strategyBPrompt').value,
    evaluator_prompt: document.getElementById('evaluatorPrompt').value,
  };

  try {
    const res = await fetch(`${API}/api/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || 'request failed');
    }

    outputA.textContent = data.output_a;
    outputB.textContent = data.output_b;
    evaluationOut.textContent = JSON.stringify(data.evaluation, null, 2);
    lastRun = { ...payload, ...data };
  } catch (error) {
    outputA.textContent = '';
    outputB.textContent = '';
    evaluationOut.textContent = `Error: ${error.message}`;
  }
});

const cliOut = document.getElementById('cliOut');
for (const btn of document.querySelectorAll('.cliBtn')) {
  btn.addEventListener('click', async () => {
    cliOut.textContent = 'Executing...';
    const payload = {
      command: btn.dataset.command,
      file_id: document.getElementById('fileId').value.trim(),
      job_id: document.getElementById('jobId').value.trim(),
      model: document.getElementById('baseModel').value.trim(),
    };

    try {
      const res = await fetch(`${API}/api/cli`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      cliOut.textContent = `return_code: ${data.return_code}\n\nstdout:\n${data.stdout || '(none)'}\n\nstderr:\n${data.stderr || '(none)'}`;
    } catch (error) {
      cliOut.textContent = `Error: ${error.message}`;
    }
  });
}

const marketList = document.getElementById('marketList');

function loadMarket() {
  const items = JSON.parse(localStorage.getItem(MARKET_KEY) || '[]');
  marketList.innerHTML = '';
  items.forEach((item, idx) => {
    const li = document.createElement('li');
    li.innerHTML = `<strong>${item.name}</strong> [${item.role}] <button data-idx="${idx}">Use</button><div>${item.text}</div>`;
    marketList.appendChild(li);
  });

  for (const useBtn of marketList.querySelectorAll('button')) {
    useBtn.addEventListener('click', () => {
      const items2 = JSON.parse(localStorage.getItem(MARKET_KEY) || '[]');
      const item = items2[Number(useBtn.dataset.idx)];
      if (!item) return;
      if (item.role === 'strategy_a') document.getElementById('strategyAPrompt').value = item.text;
      if (item.role === 'strategy_b') document.getElementById('strategyBPrompt').value = item.text;
      if (item.role === 'evaluator') document.getElementById('evaluatorPrompt').value = item.text;
    });
  }
}

document.getElementById('saveTemplate').addEventListener('click', () => {
  const name = document.getElementById('templateName').value.trim();
  const role = document.getElementById('templateRole').value;
  const text = document.getElementById('templateText').value.trim();
  if (!name || !text) return;
  const items = JSON.parse(localStorage.getItem(MARKET_KEY) || '[]');
  items.unshift({ name, role, text });
  localStorage.setItem(MARKET_KEY, JSON.stringify(items.slice(0, 30)));
  loadMarket();
});

const examplesRoot = document.getElementById('examples');

function addExample(system = '', user = '', assistant = '') {
  const card = document.createElement('div');
  card.className = 'example-card';
  card.innerHTML = `
    <label>System<input class="sys" value="${system.replaceAll('"', '&quot;')}" placeholder="You are a helpful assistant." /></label>
    <label>User<textarea class="usr" rows="2">${user}</textarea></label>
    <label>Assistant<textarea class="ast" rows="2">${assistant}</textarea></label>
    <button class="remove">Remove</button>
  `;
  card.querySelector('.remove').addEventListener('click', () => card.remove());
  examplesRoot.appendChild(card);
}

document.getElementById('addExample').addEventListener('click', () => addExample());
document.getElementById('exportJsonl').addEventListener('click', () => {
  const lines = [];
  for (const card of examplesRoot.querySelectorAll('.example-card')) {
    const system = card.querySelector('.sys').value.trim();
    const user = card.querySelector('.usr').value.trim();
    const assistant = card.querySelector('.ast').value.trim();
    if (!system || !user || !assistant) continue;
    lines.push(JSON.stringify({
      messages: [
        { role: 'system', content: system },
        { role: 'user', content: user },
        { role: 'assistant', content: assistant },
      ],
    }));
  }
  document.getElementById('jsonlOut').value = lines.join('\n');
});

addExample('You are a helpful assistant.', 'How should I structure an opening statement?', 'Start with theme, timeline, evidence, and requested conclusion.');
loadMarket();
renderVotes();
