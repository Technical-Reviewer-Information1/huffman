/* 画面まわり */
(function () {
  'use strict';
  const H = window.Huffman, TV = window.TreeView;
  const $ = id => document.getElementById(id);

  const S = {
    inputMode: 'text',
    buildMode: 'self',
    freq: new Map(),
    pool: [],            // 自分で組み立てるモードの残りカード
    history: [],         // undo 用
    selected: [],
    solution: null,      // {root, codes, steps}
    root: null,
    codes: null,
    autoIndex: 0,
    timer: null,
    quiz: null,
    qScore: 0, qTotal: 0
  };

  /* ============ STEP 1 ============ */
  function setInputMode(m) {
    S.inputMode = m;
    $('modeText').setAttribute('aria-pressed', m === 'text');
    $('modeManual').setAttribute('aria-pressed', m === 'manual');
    $('paneText').hidden = m !== 'text';
    $('paneManual').hidden = m !== 'manual';
    recompute();
  }

  function readPairs() {
    const map = new Map();
    let dup = false, bad = false;
    [...$('pairs').children].forEach(row => {
      const ch = row.querySelector('.p-ch').value;
      const n = parseInt(row.querySelector('.p-n').value, 10);
      if (ch === '' ) return;
      const c = [...ch][0];
      if (!Number.isFinite(n) || n <= 0) { bad = true; return; }
      if (map.has(c)) { dup = true; return; }
      map.set(c, n);
    });
    return { map, dup, bad };
  }

  function addPairRow(ch, n) {
    const row = document.createElement('div');
    row.className = 'pair';
    row.innerHTML =
      '<input type="text" class="p-ch mono" maxlength="2" placeholder="文字" aria-label="文字">' +
      '<input type="number" class="p-n" min="1" step="1" placeholder="回数" aria-label="出現回数">' +
      '<button class="del" title="この行を削除" aria-label="この行を削除">×</button>';
    row.querySelector('.p-ch').value = ch || '';
    row.querySelector('.p-n').value = n || '';
    row.querySelector('.del').addEventListener('click', () => { row.remove(); recompute(); });
    row.addEventListener('input', recompute);
    $('pairs').appendChild(row);
  }

  function setPreset(str) {
    $('pairs').innerHTML = '';
    str.split(',').forEach(p => { const [c, n] = p.split(':'); addPairRow(c, n); });
    recompute();
  }

  function recompute() {
    let map, msg = '';
    if (S.inputMode === 'text') {
      const t = $('inputText').value;
      map = H.countChars(t);
      if (t.length === 0) msg = '文章を入力してください。';
      else if (map.size < 2) msg = 'ハフマン符号化には <strong>2種類以上</strong> の文字が必要です。ちがう文字を足してみましょう。';
    } else {
      const r = readPairs();
      map = r.map;
      if (r.dup) msg = '同じ文字が複数の行にあります。1文字につき1行にしてください。';
      else if (r.bad) msg = '出現回数は <strong>1以上の整数</strong> で入力してください。';
      else if (map.size < 2) msg = '文字を <strong>2種類以上</strong> 入力してください。';
    }
    $('err1').innerHTML = msg;
    $('err1').hidden = !msg;

    S.freq = map;
    drawFreq(map);
    $('mKinds').textContent = map.size;
    $('mTotal').textContent = [...map.values()].reduce((a, b) => a + b, 0);

    S.solution = (!msg && map.size >= 2) ? H.build(map) : null;
    resetBuild();
  }

  function drawFreq(map) {
    const box = $('freqBars');
    box.innerHTML = '';
    if (map.size === 0) { box.innerHTML = '<p style="color:var(--ink-3);font-size:.86rem">データがありません</p>'; return; }
    const max = Math.max(...map.values());
    const total = [...map.values()].reduce((a, b) => a + b, 0);
    [...map.entries()].sort((a, b) => b[1] - a[1]).forEach(([ch, n]) => {
      const d = document.createElement('div');
      d.className = 'freqbar';
      d.innerHTML = '<span class="ch"></span><span class="track"><span class="fill"></span></span>' +
        '<span class="n">' + n + '<span style="color:var(--ink-3)"> (' + Math.round(n / total * 100) + '%)</span></span>';
      d.querySelector('.ch').textContent = TV.displayChar(ch);
      box.appendChild(d);
      setTimeout(() => { d.querySelector('.fill').style.width = (n / max * 100) + '%'; }, 30);
    });
  }

  /* ============ STEP 2 ============ */
  function setBuildMode(m) {
    S.buildMode = m;
    $('modeSelf').setAttribute('aria-pressed', m === 'self');
    $('modeAuto').setAttribute('aria-pressed', m === 'auto');
    $('autoCtrl').hidden = m !== 'auto';
    ['mergeBtn', 'undoBtn'].forEach(id => $(id).style.display = m === 'self' ? '' : 'none');
    resetBuild();
  }

  function resetBuild() {
    stopAuto();
    S.selected = []; S.history = []; S.autoIndex = 0;
    S.root = null; S.codes = null;
    if (S.solution) {
      // 自分用に新しいノード集合を作る
      const fresh = H.build(S.freq);
      S.pool = fresh.steps[0].pool.slice();
    } else {
      S.pool = [];
    }
    lockResults();
    if (S.buildMode === 'auto') renderAuto(); else renderPool();
  }

  function renderPool() {
    const pool = $('pool');
    pool.innerHTML = '';
    if (S.pool.length === 0) {
      pool.innerHTML = '<p style="color:var(--ink-3);font-size:.86rem;margin:auto">STEP 1 でデータを入力してください。</p>';
    }
    S.pool.forEach(n => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'node-card ' + (n.ch !== null ? 'leaf' : 'internal');
      b.setAttribute('aria-pressed', S.selected.includes(n.id));
      b.dataset.id = n.id;
      const label = n.ch !== null ? TV.displayChar(n.ch) : '●';
      b.innerHTML = '<span class="label"></span><span class="freq">' + n.freq + '</span>';
      b.querySelector('.label').textContent = label;
      b.addEventListener('click', () => toggleSelect(n));
      pool.appendChild(b);
    });
    $('poolCount').textContent = S.pool.length + '枚';
    $('mergeCount').textContent = '結合 ' + S.history.length + ' 回';
    $('mergeBtn').disabled = S.selected.length !== 2;
    $('undoBtn').disabled = S.history.length === 0;
    drawForest($('treeBuild'), S.pool);
  }

  function toggleSelect(n) {
    if (S.buildMode !== 'self') return;
    const i = S.selected.indexOf(n.id);
    if (i >= 0) S.selected.splice(i, 1);
    else { if (S.selected.length >= 2) S.selected.shift(); S.selected.push(n.id); }
    hideFb();
    renderPool();
  }

  function doMerge() {
    const [a, b] = S.selected.map(id => S.pool.find(n => n.id === id));
    if (!a || !b) return;
    if (!H.isValidPair(S.pool, a, b)) {
      const sorted = S.pool.map(n => n.freq).sort((x, y) => x - y);
      showFb('ng', 'まだ小さいカードが残っています。いま選べる最小は <strong class="mono">' +
        sorted[0] + '</strong> と <strong class="mono">' + sorted[1] +
        '</strong> です（選んだのは ' + a.freq + ' と ' + b.freq + '）。');
      document.querySelectorAll('.node-card[aria-pressed="true"]').forEach(el => {
        el.classList.remove('shake'); void el.offsetWidth; el.classList.add('shake');
      });
      return;
    }
    S.history.push(S.pool.slice());
    const parent = H.merge(a, b);
    S.pool = S.pool.filter(n => n !== a && n !== b).concat([parent]);
    S.selected = [];
    const l = parent.left, r = parent.right;
    showFb('ok', 'いいですね。<strong class="mono">' + l.freq + '</strong> を左（0）、<strong class="mono">' +
      r.freq + '</strong> を右（1）にして、合計 <strong class="mono">' + parent.freq + '</strong> の新しいカードができました。');
    renderPool();
    if (S.pool.length === 1) complete(S.pool[0]);
  }

  function undo() {
    if (!S.history.length) return;
    S.pool = S.history.pop();
    S.selected = [];
    hideFb();
    lockResults();
    renderPool();
  }

  /* --- お手本モード --- */
  function renderAuto() {
    if (!S.solution) { $('pool').innerHTML = ''; $('stepLabel').textContent = 'ステップ 0 / 0'; drawForest($('treeBuild'), []); return; }
    const steps = S.solution.steps;
    const i = Math.min(S.autoIndex, steps.length - 1);
    const st = steps[i];
    const pool = $('pool');
    pool.innerHTML = '';
    st.pool.forEach(n => {
      const isNew = st.merged && n === st.merged;
      const d = document.createElement('div');
      d.className = 'node-card ' + (n.ch !== null ? 'leaf' : 'internal');
      d.setAttribute('aria-pressed', isNew ? 'true' : 'false');
      d.innerHTML = '<span class="label"></span><span class="freq">' + n.freq + '</span>';
      d.querySelector('.label').textContent = n.ch !== null ? TV.displayChar(n.ch) : '●';
      pool.appendChild(d);
    });
    $('poolCount').textContent = st.pool.length + '枚';
    $('stepLabel').textContent = 'ステップ ' + i + ' / ' + (steps.length - 1);
    $('prevStep').disabled = i === 0;
    $('nextStep').disabled = i === steps.length - 1;
    if (st.picked) {
      showFb('info', '最小の <strong class="mono">' + st.picked[0].freq + '</strong> と <strong class="mono">' +
        st.picked[1].freq + '</strong> を選び、合計 <strong class="mono">' + st.merged.freq + '</strong> にまとめました。');
    } else {
      showFb('info', 'すべての文字をカードにして並べました。ここから小さい2枚ずつ結合していきます。');
    }
    drawForest($('treeBuild'), st.pool);
    if (i === steps.length - 1) complete(st.pool[0]); else lockResults();
  }

  function stepTo(i) {
    if (!S.solution) return;
    S.autoIndex = Math.max(0, Math.min(i, S.solution.steps.length - 1));
    renderAuto();
  }
  function playAuto() {
    if (S.timer) { stopAuto(); return; }
    if (!S.solution) return;
    if (S.autoIndex >= S.solution.steps.length - 1) S.autoIndex = 0;
    $('playBtn').textContent = '⏸ 停止';
    S.timer = setInterval(() => {
      if (S.autoIndex >= S.solution.steps.length - 1) { stopAuto(); return; }
      stepTo(S.autoIndex + 1);
    }, 1400);
  }
  function stopAuto() {
    if (S.timer) clearInterval(S.timer);
    S.timer = null;
    const b = $('playBtn'); if (b) b.textContent = '▶ 自動再生';
  }

  function drawForest(box, roots) {
    box.innerHTML = '';
    const trees = roots.filter(n => n.ch === null);
    if (trees.length === 0) {
      box.innerHTML = '<p style="color:var(--ink-3);font-size:.86rem;padding:18px;text-align:center">' +
        'まだ結合していないので木はありません。カードを2枚くっつけると、ここに木が育ちます。</p>';
      return;
    }
    const row = document.createElement('div');
    row.style.cssText = 'display:flex;gap:22px;align-items:flex-start;padding:10px;min-width:min-content';
    trees.forEach(t => {
      const c = document.createElement('div');
      TV.render(c, { root: t, showCodes: false });
      row.appendChild(c);
    });
    box.appendChild(row);
  }

  function showFb(kind, html) {
    const n = $('fb2');
    n.className = 'note ' + kind;
    n.innerHTML = html;
    n.hidden = false;
  }
  function hideFb() { $('fb2').hidden = true; }

  /* ============ STEP 3-5 ============ */
  function lockResults() {
    ['3', '4', '5'].forEach(i => { $('lock' + i).hidden = false; $('body' + i).hidden = true; });
  }

  function complete(root) {
    S.root = root;
    S.codes = H.buildCodes(root);
    ['3', '4', '5'].forEach(i => { $('lock' + i).hidden = true; $('body' + i).hidden = false; });
    renderFinal();
    renderCompare();
    initTryOut();
    newQuestion();
  }

  function renderFinal() {
    TV.render($('treeFinal'), { root: S.root, codes: S.codes, showCodes: true });
    const tb = $('codeTable');
    tb.innerHTML = '';
    const rows = [...S.freq.entries()].sort((a, b) => b[1] - a[1]);
    rows.forEach(([ch, n]) => {
      const code = S.codes[ch];
      const tr = document.createElement('tr');
      tr.innerHTML = '<td class="mono"></td><td>' + n + '</td><td class="mono code"></td><td>' +
        code.length + '</td><td>' + (code.length * n) + '</td>';
      tr.children[0].textContent = TV.displayChar(ch);
      tr.querySelector('.code').innerHTML = colorBits(code);
      tb.appendChild(tr);
    });

    const sorted = rows.slice();
    const most = sorted[0], least = sorted[sorted.length - 1];
    const lens = rows.map(([c]) => S.codes[c].length);
    $('insight').innerHTML =
      '<ul style="margin:0;padding-left:1.15em;font-size:.9rem;line-height:1.95;color:var(--ink-2)">' +
      '<li>いちばん多い <strong class="mono">' + TV.displayChar(most[0]) + '</strong>（' + most[1] + '回）の符号は <strong class="mono">' +
      S.codes[most[0]].length + 'ビット</strong>。</li>' +
      '<li>いちばん少ない <strong class="mono">' + TV.displayChar(least[0]) + '</strong>（' + least[1] + '回）の符号は <strong class="mono">' +
      S.codes[least[0]].length + 'ビット</strong>。</li>' +
      '<li>符号の長さは <strong>' + Math.min(...lens) + '〜' + Math.max(...lens) + 'ビット</strong> にばらけています。これが<strong>可変長</strong>ということ。</li>' +
      '<li>どの符号も、ほかの符号の<strong>先頭にはなっていません</strong>。だから区切り記号なしで復号できます。</li>' +
      '</ul>';
  }

  function colorBits(code) {
    return [...code].map(b => '<span class="bit' + b + '">' + b + '</span>').join('');
  }

  function renderCompare() {
    const kinds = S.freq.size;
    const total = [...S.freq.values()].reduce((a, b) => a + b, 0);
    const fb = H.fixedBits(kinds);
    const fTotal = fb * total;
    let hTotal = 0;
    S.freq.forEach((n, ch) => { hTotal += S.codes[ch].length * n; });
    const saved = fTotal - hTotal;
    const ratio = fTotal ? hTotal / fTotal * 100 : 0;      // 本書の定義：圧縮後 ÷ 圧縮前 × 100
    const cut = fTotal ? saved / fTotal * 100 : 0;

    $('fbits').textContent = fb;
    $('fTotal').textContent = fTotal + ' ビット';
    $('hAvg').textContent = (hTotal / total).toFixed(2);
    $('hTotal').textContent = hTotal + ' ビット';
    $('mSaved').textContent = saved;
    $('mRatio').textContent = ratio.toFixed(1) + '%';
    $('mAfter').textContent = cut.toFixed(1) + '%';
    const max = Math.max(fTotal, hTotal) || 1;
    setTimeout(() => {
      $('fFill').style.width = (fTotal / max * 100) + '%';
      $('fFill').textContent = fTotal + 'b';
      $('hFill').style.width = (hTotal / max * 100) + '%';
      $('hFill').textContent = hTotal + 'b';
    }, 30);
  }

  /* --- 符号化・復号 --- */
  let decodeStep = 0;
  function initTryOut() {
    const sample = [...S.freq.keys()].slice(0, 3).join('');
    $('encIn').value = sample;
    doEncode();
    const bits = H.encode(sample, S.codes) || '';
    $('decIn').value = bits;
    decodeStep = 0;
    doDecode();
  }

  function doEncode() {
    const t = $('encIn').value;
    if (!t) { $('encOut').textContent = '—'; $('encStat').textContent = ''; return; }
    const bits = H.encode(t, S.codes);
    if (bits === null) {
      const bad = [...t].filter(c => !(c in S.codes));
      $('encOut').innerHTML = '<span style="color:var(--ng)">符号表にない文字があります：' +
        [...new Set(bad)].map(c => '<span class="chip">' + TV.displayChar(c) + '</span>').join('') + '</span>';
      $('encStat').textContent = '';
      return;
    }
    $('encOut').innerHTML = [...t].map(c =>
      '<span class="g" title="' + c + '">' + colorBits(S.codes[c]) + '</span>').join('');
    const ascii = [...t].length * 8;
    $('encStat').innerHTML = [...t].length + ' 文字 → <strong>' + bits.length + ' ビット</strong>' +
      '（1文字8ビットなら ' + ascii + ' ビット）';
  }

  function doDecode(highlightOnly) {
    const bits = $('decIn').value.replace(/\s+/g, '');
    if (!bits) { $('decOut').textContent = '—'; TV.render($('treeDecode'), { root: S.root, codes: S.codes, showCodes: true }); return; }
    const res = H.decode(bits, S.root);
    if (res.error === 'bit') {
      $('decOut').innerHTML = '<span style="color:var(--ng)">0 と 1 だけを入力してください。</span>';
      return;
    }
    const shown = Math.min(decodeStep, res.path.length);
    let html = res.path.slice(0, shown === 0 ? res.path.length : shown)
      .map((p, i) => '<span class="g' + (shown && i === shown - 1 ? ' hot' : '') + '">' +
        colorBits(p.bits) + ' → <strong>' + TV.displayChar(p.ch) + '</strong></span>').join('');
    if (res.error === 'incomplete') {
      html += '<div style="color:var(--warn);margin-top:6px">最後のビットが途中で終わっています（木の葉まで届いていません）。</div>';
    } else if (res.error === 'path') {
      html += '<div style="color:var(--ng);margin-top:6px">その進み方の枝は木にありません。</div>';
    } else if (shown === 0 || shown === res.path.length) {
      html += '<div style="margin-top:8px;font-weight:800">復号結果： <span class="mono">' +
        [...(res.text || '')].map(TV.displayChar).join('') + '</span></div>';
    }
    $('decOut').innerHTML = html || '—';

    let path = [];
    if (shown > 0 && shown <= res.path.length) {
      path = TV.pathTo(S.root, res.path[shown - 1].ch);
    }
    TV.render($('treeDecode'), { root: S.root, codes: S.codes, showCodes: true, highlightPath: path });
  }

  /* --- クイズ --- */
  function newQuestion() {
    if (!S.codes) return;
    const chars = [...S.freq.keys()];
    const types = chars.length >= 3 ? [0, 1, 2] : [0, 2];
    const t = types[Math.floor(Math.random() * types.length)];
    let q;
    if (t === 0) {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      const ans = S.codes[ch];
      const pool = [...new Set(Object.values(S.codes).concat(['0' + ans, ans + '1', ans.split('').reverse().join('')]))]
        .filter(c => c !== ans);
      q = { text: '「' + TV.displayChar(ch) + '」の符号はどれ？', ans: ans, choices: shuffle([ans].concat(pool.slice(0, 3))) };
    } else if (t === 1) {
      const pick = shuffle(chars).slice(0, 2);
      const bits = pick.map(c => S.codes[c]).join('');
      const ans = pick.join('');
      const wrongs = new Set();
      while (wrongs.size < 3) {
        const w = shuffle(chars).slice(0, 2).join('');
        if (w !== ans) wrongs.add(w);
        if (wrongs.size > 20) break;
      }
      q = {
        text: '符号列 ' + bits.split('').map(b => '<span class="bit' + b + '">' + b + '</span>').join('') + ' を復号すると？',
        ans: ans, choices: shuffle([ans].concat([...wrongs]))
      };
    } else {
      const ch = chars[Math.floor(Math.random() * chars.length)];
      const ans = String(S.codes[ch].length) + ' ビット';
      const set = new Set([ans]);
      [1, 2, 3, 4, 5].forEach(k => { if (set.size < 4) set.add(k + ' ビット'); });
      q = { text: '「' + TV.displayChar(ch) + '」1文字を送るのに必要なビット数は？', ans: ans, choices: shuffle([...set]).slice(0, 4) };
    }
    if (!q.choices.includes(q.ans)) q.choices[0] = q.ans;
    S.quiz = q;
    $('qText').innerHTML = q.text;
    const box = $('qChoices');
    box.innerHTML = '';
    q.choices.forEach(c => {
      const b = document.createElement('button');
      b.className = 'btn';
      b.innerHTML = /^[01]+$/.test(c) ? colorBits(c) : escapeHtml(c);
      b.addEventListener('click', () => answer(b, c));
      box.appendChild(b);
    });
    $('qFb').hidden = true;
  }

  function answer(btn, c) {
    if (btn.parentElement.classList.contains('locked')) return;
    btn.parentElement.classList.add('locked');
    S.qTotal++;
    const ok = c === S.quiz.ans;
    if (ok) S.qScore++;
    btn.classList.add(ok ? 'correct' : 'wrong');
    if (!ok) {
      [...btn.parentElement.children].forEach(b => {
        if (b.textContent.replace(/\s/g, '') === S.quiz.ans.replace(/\s/g, '')) b.classList.add('correct');
      });
    }
    const fb = $('qFb');
    fb.className = 'note ' + (ok ? 'ok' : 'ng');
    fb.innerHTML = ok ? '正解！' : '正解は <strong class="mono">' + escapeHtml(S.quiz.ans) + '</strong> です。符号表と木をもう一度見てみましょう。';
    fb.hidden = false;
    $('qScore').textContent = S.qScore;
    $('qTotal').textContent = S.qTotal;
  }

  function shuffle(a) { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
  function escapeHtml(s) { return String(s).replace(/[&<>"]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m])); }

  /* ============ 起動 ============ */
  /* 本文の問題 */
  function drawBook() {
    if (!document.getElementById('bookBox')) return;
    window.Quiz.choice('bookBox', 'bookNote', [{"k": "ア", "q": "A〜Dの4種類を固定長符号で表すには、1文字あたり少なくとも何ビット必要か。", "ch": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "a": 2, "why": "2¹＝2では足りず、2²＝4でちょうど4種類を表せるので<strong>2ビット</strong>です。"}, {"k": "イウ", "q": "20文字を固定長符号で表すと、圧縮前のデータ量は何ビットか。（十の位＝イ、一の位＝ウ）", "ch": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "a": 4, "why": "2ビット × 20文字 ＝ <strong>40ビット</strong>。十の位は 4 です。"}, {"k": "エオ", "q": "ハフマン符号化した後のデータ量は何ビットか。（十の位＝エ、一の位＝オ）", "ch": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "a": 3, "why": "A:6×2＋B:3×3＋C:10×1＋D:1×3 ＝ 12＋9＋10＋3 ＝ <strong>34ビット</strong>。十の位は 3 です。"}, {"k": "キ", "q": "「AAAAAAAABBBBCCCDDEEF」の圧縮率（圧縮後÷圧縮前×100）は何％か。", "ch": ["58", "68", "78", "88"], "a": 2, "why": "固定長は6種類なので3ビット×20＝60ビット。ハフマンでは47ビットなので 47÷60×100 ＝ 78.3… ≒ <strong>78％</strong>です。STEP 4 で確かめられます。"}], "本文の答えは【ア】②　【イ】④　【ウ】⓪　【エ】③　【オ】④　【カ】⓪　【キ】② です。");
  }

  function init() {
    $('modeText').addEventListener('click', () => setInputMode('text'));
    $('modeManual').addEventListener('click', () => setInputMode('manual'));
    $('inputText').addEventListener('input', recompute);
    document.querySelectorAll('[data-sample]').forEach(b =>
      b.addEventListener('click', () => { $('inputText').value = b.dataset.sample; recompute(); }));
    document.querySelectorAll('[data-preset]').forEach(b =>
      b.addEventListener('click', () => setPreset(b.dataset.preset)));
    $('addPair').addEventListener('click', () => addPairRow('', ''));
    setPreset('A:6,B:3,C:10,D:1');

    $('modeSelf').addEventListener('click', () => setBuildMode('self'));
    $('modeAuto').addEventListener('click', () => setBuildMode('auto'));
    $('mergeBtn').addEventListener('click', doMerge);
    $('undoBtn').addEventListener('click', undo);
    $('resetBtn').addEventListener('click', resetBuild);
    $('prevStep').addEventListener('click', () => { stopAuto(); stepTo(S.autoIndex - 1); });
    $('nextStep').addEventListener('click', () => { stopAuto(); stepTo(S.autoIndex + 1); });
    $('playBtn').addEventListener('click', playAuto);

    $('encIn').addEventListener('input', doEncode);
    $('decIn').addEventListener('input', () => { decodeStep = 0; doDecode(); });
    $('stepDecode').addEventListener('click', () => { decodeStep++; doDecode(); });
    $('resetDecode').addEventListener('click', () => { decodeStep = 0; doDecode(); });
    $('qNext').addEventListener('click', newQuestion);

    setInputMode('text');
    drawBook();
    if (window.Terms) { window.Terms.glossary(document.getElementById('glossBox'), ["ハフマン符号化", "可変長符号", "固定長符号", "語頭符号", "圧縮率", "可逆圧縮", "非可逆圧縮"]); window.Terms.attach(); }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
