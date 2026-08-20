/* ハフマン符号化のアルゴリズム本体（UI から独立） */
(function (global) {
  'use strict';

  let seqCounter = 0;
  function makeLeaf(ch, freq) {
    return { id: 'n' + (seqCounter++), ch: ch, freq: freq, left: null, right: null };
  }
  function makeInternal(a, b) {
    return { id: 'n' + (seqCounter++), ch: null, freq: a.freq + b.freq, left: a, right: b };
  }

  /** 文字列 → {文字: 出現回数}（出現順を保つ） */
  function countChars(text) {
    const map = new Map();
    for (const ch of text) map.set(ch, (map.get(ch) || 0) + 1);
    return map;
  }

  /** プール内で「次に結合すべき2つ」を返す（頻度が小さい順・同点は先に作られた順） */
  function pickSmallestTwo(pool) {
    const sorted = pool.slice().sort(cmp);
    return [sorted[0], sorted[1]];
  }
  function cmp(a, b) {
    if (a.freq !== b.freq) return a.freq - b.freq;
    return idNum(a) - idNum(b);
  }
  function idNum(n) { return parseInt(n.id.slice(1), 10); }

  /**
   * 選んだ2つが「最小の2つ」として正しいか判定する。
   * 同じ頻度が複数ある場合はどれを選んでも正解とする（教科書どおり）。
   */
  function isValidPair(pool, a, b) {
    if (!a || !b || a === b || pool.length < 2) return false;
    const freqs = pool.map(n => n.freq).sort((x, y) => x - y);
    const target = [freqs[0], freqs[1]].sort((x, y) => x - y);
    const chosen = [a.freq, b.freq].sort((x, y) => x - y);
    return chosen[0] === target[0] && chosen[1] === target[1];
  }

  /** 結合。頻度が小さいほうを左（=0）に置く */
  function merge(a, b) {
    const [l, r] = cmp(a, b) <= 0 ? [a, b] : [b, a];
    return makeInternal(l, r);
  }

  /** 木から符号表を作る */
  function buildCodes(root) {
    const codes = {};
    if (!root) return codes;
    if (!root.left && !root.right) { codes[root.ch] = '0'; return codes; }
    (function walk(node, prefix) {
      if (!node) return;
      if (node.ch !== null) { codes[node.ch] = prefix; return; }
      walk(node.left, prefix + '0');
      walk(node.right, prefix + '1');
    })(root, '');
    return codes;
  }

  /** 頻度表から一気に木を作り、途中経過も記録する */
  function build(freqMap) {
    seqCounter = 0;
    const entries = [...freqMap.entries()];
    if (entries.length === 0) return null;
    let pool = entries.map(([ch, f]) => makeLeaf(ch, f));
    const steps = [{ pool: pool.slice(), merged: null, picked: null }];
    while (pool.length > 1) {
      const [a, b] = pickSmallestTwo(pool);
      const parent = merge(a, b);
      pool = pool.filter(n => n !== a && n !== b).concat([parent]);
      steps.push({ pool: pool.slice(), merged: parent, picked: [a, b] });
    }
    const root = pool[0];
    return { root: root, codes: buildCodes(root), steps: steps };
  }

  function encode(text, codes) {
    let out = '';
    for (const ch of text) {
      if (!(ch in codes)) return null;
      out += codes[ch];
    }
    return out;
  }

  /** 符号列を木でたどって復号。たどった経路も返す */
  function decode(bits, root) {
    if (!root) return { text: null, path: [] };
    const single = !root.left && !root.right;
    let node = root, out = '', path = [], acc = '';
    for (const b of bits) {
      if (b !== '0' && b !== '1') return { text: null, path: path, error: 'bit' };
      if (single) { out += root.ch; path.push({ bits: b, ch: root.ch }); continue; }
      node = (b === '0') ? node.left : node.right;
      acc += b;
      if (!node) return { text: null, path: path, error: 'path' };
      if (node.ch !== null) { out += node.ch; path.push({ bits: acc, ch: node.ch }); node = root; acc = ''; }
    }
    if (acc !== '') return { text: out, path: path, error: 'incomplete' };
    return { text: out, path: path };
  }

  /** 固定長符号での 1 文字あたりビット数 */
  function fixedBits(nKinds) {
    return Math.max(1, Math.ceil(Math.log2(Math.max(1, nKinds))));
  }

  global.Huffman = {
    countChars, build, buildCodes, encode, decode,
    isValidPair, pickSmallestTwo, merge, fixedBits, cmp
  };
})(window);
