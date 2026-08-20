/* ハフマン木を SVG で描画する */
(function (global) {
  'use strict';

  const NS = 'http://www.w3.org/2000/svg';
  const R_LEAF = 26, R_INT = 22, GAP_X = 74, GAP_Y = 92, PAD = 40;

  function el(name, attrs, text) {
    const e = document.createElementNS(NS, name);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }

  /** 葉を左から並べて座標を決める */
  function layout(root) {
    const pos = new Map();
    let cursor = 0, maxDepth = 0;
    (function walk(node, depth) {
      if (!node) return;
      maxDepth = Math.max(maxDepth, depth);
      if (!node.left && !node.right) {
        pos.set(node.id, { x: cursor++, y: depth });
        return;
      }
      walk(node.left, depth + 1);
      const leftX = node.left ? pos.get(node.left.id).x : cursor;
      walk(node.right, depth + 1);
      const rightX = node.right ? pos.get(node.right.id).x : cursor;
      pos.set(node.id, { x: (leftX + rightX) / 2, y: depth });
    })(root, 0);
    return { pos, leaves: cursor, depth: maxDepth };
  }

  /**
   * @param {Object} opts {root, codes, highlightPath:[nodeIds], showCodes:bool}
   */
  function render(container, opts) {
    container.innerHTML = '';
    const root = opts.root;
    if (!root) return;
    const { pos, leaves, depth } = layout(root);
    const W = Math.max(320, (leaves - 1) * GAP_X + PAD * 2 + 40);
    const H = depth * GAP_Y + PAD * 2 + 40;
    const svg = el('svg', {
      viewBox: `0 0 ${W} ${H}`, width: W, height: H,
      role: 'img', 'aria-label': 'ハフマン木'
    });
    const X = i => PAD + 20 + i * GAP_X;
    const Y = d => PAD + d * GAP_Y;
    const hot = new Set(opts.highlightPath || []);

    // --- 枝 ---
    (function edges(node) {
      if (!node || node.ch !== null) return;
      const p = pos.get(node.id);
      [['left', '0'], ['right', '1']].forEach(([side, bit]) => {
        const c = node[side];
        if (!c) return;
        const q = pos.get(c.id);
        const isHot = hot.has(node.id) && hot.has(c.id);
        svg.appendChild(el('line', {
          x1: X(p.x), y1: Y(p.y), x2: X(q.x), y2: Y(q.y),
          class: 'edge e' + bit + (isHot ? ' hot' : '')
        }));
        const mx = (X(p.x) + X(q.x)) / 2, my = (Y(p.y) + Y(q.y)) / 2;
        svg.appendChild(el('rect', {
          x: mx - 11, y: my - 11, width: 22, height: 22, rx: 6,
          class: 'bitbg b' + bit
        }));
        svg.appendChild(el('text', { x: mx, y: my + 1, class: 't-bit b' + bit }, bit));
        edges(c);
      });
    })(root);

    // --- ノード ---
    (function nodes(node) {
      if (!node) return;
      const p = pos.get(node.id);
      const leaf = node.ch === null ? false : true;
      const r = leaf ? R_LEAF : R_INT;
      svg.appendChild(el('circle', {
        cx: X(p.x), cy: Y(p.y), r: r,
        class: (leaf ? 'nd-leaf' : 'nd-int') + (hot.has(node.id) ? ' nd-hot' : '')
      }));
      if (leaf) {
        svg.appendChild(el('text', { x: X(p.x), y: Y(p.y) - 5, class: 't-ch' }, displayChar(node.ch)));
        svg.appendChild(el('text', { x: X(p.x), y: Y(p.y) + 11, class: 't-fq' }, node.freq));
        if (opts.showCodes && opts.codes && opts.codes[node.ch] != null) {
          svg.appendChild(el('text', { x: X(p.x), y: Y(p.y) + r + 15, class: 't-code' }, opts.codes[node.ch]));
        }
      } else {
        svg.appendChild(el('text', { x: X(p.x), y: Y(p.y) + 1, class: 't-fq' }, node.freq));
      }
      nodes(node.left); nodes(node.right);
    })(root);

    container.appendChild(svg);
  }

  function displayChar(ch) {
    if (ch === ' ') return '␣';
    if (ch === '\n') return '⏎';
    if (ch === '\t') return '⇥';
    return ch;
  }

  /** 根から目的の葉までのノード ID 列 */
  function pathTo(root, targetCh) {
    const out = [];
    return (function walk(node) {
      if (!node) return null;
      out.push(node.id);
      if (node.ch === targetCh) return out.slice();
      const l = node.left ? walk(node.left) : null;
      if (l) return l;
      const r = node.right ? walk(node.right) : null;
      if (r) return r;
      out.pop();
      return null;
    })(root) || [];
  }

  global.TreeView = { render, pathTo, displayChar };
})(window);
