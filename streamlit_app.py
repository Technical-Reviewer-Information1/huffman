import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import heapq
import numpy as np
from typing import Dict, List, Tuple, Optional
import math

# ハフマンノードクラス
class HuffmanNode:
    def __init__(self, char: str, freq: int, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
        self.code = ""
        self.id = f"{char}_{freq}" if char else f"internal_{freq}"
    
    def __lt__(self, other):
        return self.freq < other.freq

# ハフマン符号化クラス
class HuffmanCoding:
    def __init__(self):
        self.root = None
        self.codes = {}
        self.steps = []
        self.tree_positions = {}
    
    def build_tree(self, frequency_dict: Dict[str, int]) -> Tuple[HuffmanNode, List]:
        if len(frequency_dict) == 0:
            return None, []
        
        if len(frequency_dict) == 1:
            # 文字が1つの場合の特別処理
            char = list(frequency_dict.keys())[0]
            freq = frequency_dict[char]
            root = HuffmanNode(char, freq)
            self.codes = {char: "0"}
            return root, [{"step": 1, "description": f"文字が1つのため、'{char}'に'0'を割り当て", "nodes": [root]}]
        
        heap = []
        steps = []
        node_counter = 0
        
        # 初期ノード作成
        for char, freq in frequency_dict.items():
            node = HuffmanNode(char, freq)
            heapq.heappush(heap, node)
        
        # ステップ1: 初期状態
        steps.append({
            "step": 1,
            "description": "文字と頻度をノードとして初期化",
            "nodes": list(heap),
            "action": "init"
        })
        
        step_counter = 2
        
        # ツリー構築
        while len(heap) > 1:
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            merged_freq = left.freq + right.freq
            merged_node = HuffmanNode(None, merged_freq, left, right)
            merged_node.id = f"merged_{node_counter}"
            node_counter += 1
            
            steps.append({
                "step": step_counter,
                "description": f"頻度{left.freq}と{right.freq}のノードを結合 → 新ノード(頻度{merged_freq})",
                "nodes": list(heap) + [merged_node],
                "merged_nodes": [left, right],
                "new_node": merged_node,
                "action": "merge"
            })
            
            heapq.heappush(heap, merged_node)
            step_counter += 1
        
        self.root = heap[0]
        self.steps = steps
        
        # 符号生成
        self._generate_codes(self.root, "")
        
        return self.root, steps
    
    def _generate_codes(self, node: HuffmanNode, code: str):
        if node:
            if node.char:  # 葉ノード
                self.codes[node.char] = code if code else "0"
            else:
                self._generate_codes(node.left, code + "0")
                self._generate_codes(node.right, code + "1")

# ツリー可視化関数
def create_tree_visualization(step_data: dict, width=800, height=600):
    fig = go.Figure()
    
    if step_data["action"] == "init":
        # 初期状態の表示
        nodes = step_data["nodes"]
        x_positions = np.linspace(0.1, 0.9, len(nodes))
        
        for i, node in enumerate(nodes):
            fig.add_trace(go.Scatter(
                x=[x_positions[i]], y=[0.5],
                mode='markers+text',
                marker=dict(size=50, color='lightblue', line=dict(width=2, color='darkblue')),
                text=f"{node.char}<br>({node.freq})",
                textposition="middle center",
                name=f"Node {node.char}",
                showlegend=False
            ))
    
    elif step_data["action"] == "merge":
        # マージステップの表示
        remaining_nodes = [n for n in step_data["nodes"] if n != step_data["new_node"]]
        merged_nodes = step_data["merged_nodes"]
        new_node = step_data["new_node"]
        
        # 残りのノード
        if remaining_nodes:
            x_pos_remaining = np.linspace(0.1, 0.4, len(remaining_nodes))
            for i, node in enumerate(remaining_nodes):
                fig.add_trace(go.Scatter(
                    x=[x_pos_remaining[i]], y=[0.2],
                    mode='markers+text',
                    marker=dict(size=40, color='lightgray'),
                    text=f"{node.char if node.char else 'merged'}<br>({node.freq})",
                    textposition="middle center",
                    showlegend=False
                ))
        
        # マージされるノード（左と右）
        fig.add_trace(go.Scatter(
            x=[0.6, 0.8], y=[0.2, 0.2],
            mode='markers+text',
            marker=dict(size=40, color='orange'),
            text=[f"{merged_nodes[0].char if merged_nodes[0].char else 'merged'}<br>({merged_nodes[0].freq})",
                  f"{merged_nodes[1].char if merged_nodes[1].char else 'merged'}<br>({merged_nodes[1].freq})"],
            textposition="middle center",
            showlegend=False
        ))
        
        # 新しいノード（親）
        fig.add_trace(go.Scatter(
            x=[0.7], y=[0.7],
            mode='markers+text',
            marker=dict(size=50, color='lightgreen', line=dict(width=3, color='darkgreen')),
            text=f"merged<br>({new_node.freq})",
            textposition="middle center",
            showlegend=False
        ))
        
        # 接続線
        fig.add_shape(type="line", x0=0.6, y0=0.2, x1=0.7, y1=0.7, 
                     line=dict(color="black", width=2))
        fig.add_shape(type="line", x0=0.8, y0=0.2, x1=0.7, y1=0.7, 
                     line=dict(color="black", width=2))
        
        # エッジラベル（0と1）
        fig.add_annotation(x=0.65, y=0.45, text="0", showarrow=False, 
                          font=dict(size=16, color="red"))
        fig.add_annotation(x=0.75, y=0.45, text="1", showarrow=False, 
                          font=dict(size=16, color="red"))
    
    fig.update_layout(
        width=width, height=height,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        title=f"ステップ {step_data['step']}: {step_data['description']}",
        title_x=0.5
    )
    
    return fig

# 最終的なハフマン木の可視化
def create_final_tree_visualization(root: HuffmanNode, codes: Dict[str, str]):
    if not root:
        return go.Figure()
    
    fig = go.Figure()
    positions = {}
    
    def calculate_positions(node, x=0.5, y=1, width=0.4, depth=0):
        if not node:
            return
        
        positions[node.id] = (x, y)
        
        if node.left or node.right:
            if node.left:
                calculate_positions(node.left, x - width/2, y - 0.15, width/2, depth + 1)
            if node.right:
                calculate_positions(node.right, x + width/2, y - 0.15, width/2, depth + 1)
    
    calculate_positions(root)
    
    # ノードの描画
    def draw_nodes(node):
        if not node:
            return
        
        x, y = positions[node.id]
        
        if node.char:  # 葉ノード
            color = 'lightcoral'
            text = f"{node.char}<br>({node.freq})<br>'{codes[node.char]}'"
        else:  # 内部ノード
            color = 'lightblue'
            text = f"({node.freq})"
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=60, color=color, line=dict(width=2, color='darkblue')),
            text=text,
            textposition="middle center",
            showlegend=False
        ))
        
        # 子ノードへの線
        if node.left:
            left_x, left_y = positions[node.left.id]
            fig.add_shape(type="line", x0=x, y0=y, x1=left_x, y1=left_y,
                         line=dict(color="black", width=2))
            # "0"ラベル
            mid_x, mid_y = (x + left_x) / 2, (y + left_y) / 2
            fig.add_annotation(x=mid_x-0.02, y=mid_y+0.02, text="0", showarrow=False,
                              font=dict(size=14, color="red"))
        
        if node.right:
            right_x, right_y = positions[node.right.id]
            fig.add_shape(type="line", x0=x, y0=y, x1=right_x, y1=right_y,
                         line=dict(color="black", width=2))
            # "1"ラベル
            mid_x, mid_y = (x + right_x) / 2, (y + right_y) / 2
            fig.add_annotation(x=mid_x+0.02, y=mid_y+0.02, text="1", showarrow=False,
                              font=dict(size=14, color="red"))
        
        draw_nodes(node.left)
        draw_nodes(node.right)
    
    draw_nodes(root)
    
    fig.update_layout(
        width=800, height=600,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        title="完成したハフマン木 (赤数字: 0=左, 1=右)",
        title_x=0.5
    )
    
    return fig

# メイン関数
def main():
    st.set_page_config(
        page_title="ハフマン符号化可視化",
        page_icon="🌳",
        layout="wide"
    )
    
    st.title("🌳 データの圧縮③ハフマン符号化")
    st.caption("Created by Dit-Lab.(Daiki ITO)")
    st.caption("Supported by Tomoaki ATSUMI")
    
    st.markdown("""
    このアプリケーションでは、ハフマン符号化のアルゴリズムを体験的に学ぶことができます。
    文字の出現頻度に応じて効率的なビット列を生成する過程を可視化します。
    """)
    
    # セッション状態の初期化
    if 'huffman' not in st.session_state:
        st.session_state.huffman = HuffmanCoding()
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'tree_built' not in st.session_state:
        st.session_state.tree_built = False
    
    # 1. データ入力セクション
    st.header("📊 1. データ（文字と頻度）の入力")
    st.write("文字とその出現回数を入力してください：")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # デフォルト値の設定
        if 'input_data' not in st.session_state:
            st.session_state.input_data = pd.DataFrame({
                '文字': ['A', 'B', 'C', 'D'],
                '出現回数': [6, 3, 10, 1]
            })
        
        # データエディタ
        edited_df = st.data_editor(
            st.session_state.input_data,
            num_rows="dynamic",
            use_container_width=True,
            key="data_editor"
        )
        
        # プリセットボタン
        col_preset1, col_preset2 = st.columns(2)
        with col_preset1:
            if st.button("📝 サンプル1"):
                st.session_state.input_data = pd.DataFrame({
                    '文字': ['A', 'B', 'C', 'D', 'E'],
                    '出現回数': [5, 9, 12, 13, 16]
                })
                st.rerun()
        
        with col_preset2:
            if st.button("📝 サンプル2"):
                st.session_state.input_data = pd.DataFrame({
                    '文字': ['あ', 'い', 'う', 'え'],
                    '出現回数': [8, 4, 2, 1]
                })
                st.rerun()
    
    with col2:
        # 入力データの可視化
        if len(edited_df) > 0:
            fig_bar = px.bar(
                edited_df,
                x='文字',
                y='出現回数',
                title="文字の出現頻度",
                color='出現回数',
                color_continuous_scale='viridis'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
    
    # データ検証
    if len(edited_df) > 0 and not edited_df['文字'].duplicated().any() and all(edited_df['出現回数'] > 0):
        frequency_dict = dict(zip(edited_df['文字'], edited_df['出現回数']))
        
        # 2. ハフマン木の構築
        st.header("🌳 2. ハフマン木の作成ステップ")
        
        col_build1, col_build2, col_build3 = st.columns([2, 2, 2])
        
        with col_build1:
            if st.button("🚀 ハフマン木を作成", type="primary"):
                st.session_state.huffman = HuffmanCoding()
                root, steps = st.session_state.huffman.build_tree(frequency_dict)
                st.session_state.root = root
                st.session_state.steps = steps
                st.session_state.current_step = 0
                st.session_state.tree_built = True
                st.rerun()
        
        if st.session_state.tree_built and 'steps' in st.session_state:
            with col_build2:
                if st.button("⬅️ 前のステップ") and st.session_state.current_step > 0:
                    st.session_state.current_step -= 1
                    st.rerun()
            
            with col_build3:
                if st.button("➡️ 次のステップ") and st.session_state.current_step < len(st.session_state.steps) - 1:
                    st.session_state.current_step += 1
                    st.rerun()
            
            # 現在のステップ表示
            if st.session_state.steps:
                current_step_data = st.session_state.steps[st.session_state.current_step]
                st.write(f"**ステップ {st.session_state.current_step + 1}/{len(st.session_state.steps)}**")
                
                if st.session_state.current_step < len(st.session_state.steps) - 1:
                    # 構築過程の表示
                    fig_step = create_tree_visualization(current_step_data)
                    st.plotly_chart(fig_step, use_container_width=True)
                else:
                    # 最終的な木の表示
                    fig_final = create_final_tree_visualization(st.session_state.root, st.session_state.huffman.codes)
                    st.plotly_chart(fig_final, use_container_width=True)
            
            # 3. 結果とデータ量の比較
            if st.session_state.huffman.codes:
                st.header("📈 3. 結果の表示とデータ量の比較")
                
                # 結果テーブル
                results_data = []
                total_bits_huffman = 0
                total_chars = sum(frequency_dict.values())
                
                for char, freq in frequency_dict.items():
                    huffman_code = st.session_state.huffman.codes[char]
                    bits_used = len(huffman_code) * freq
                    total_bits_huffman += bits_used
                    
                    results_data.append({
                        '文字': char,
                        '出現回数': freq,
                        'ハフマン符号': huffman_code,
                        'ビット長': len(huffman_code),
                        '使用ビット数': bits_used
                    })
                
                results_df = pd.DataFrame(results_data)
                
                col_result1, col_result2 = st.columns(2)
                
                with col_result1:
                    st.subheader("📊 符号化結果")
                    st.dataframe(results_df, use_container_width=True)
                
                with col_result2:
                    # 圧縮率計算
                    bits_per_char_fixed = math.ceil(math.log2(len(frequency_dict)))
                    total_bits_fixed = bits_per_char_fixed * total_chars
                    compression_ratio = (total_bits_fixed - total_bits_huffman) / total_bits_fixed * 100
                    
                    st.subheader("📊 圧縮効果")
                    
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("固定長符号化", f"{total_bits_fixed} bits", f"{bits_per_char_fixed} bits/文字")
                        st.metric("ハフマン符号化", f"{total_bits_huffman} bits", f"{total_bits_huffman/total_chars:.2f} bits/文字")
                    
                    with metrics_col2:
                        st.metric("圧縮率", f"{compression_ratio:.1f}%", f"{total_bits_fixed - total_bits_huffman} bits削減")
                        st.metric("圧縮後サイズ", f"{(100-compression_ratio):.1f}%", "元サイズとの比較")
                
                # 比較グラフ
                comparison_data = pd.DataFrame({
                    '符号化方式': ['固定長符号化', 'ハフマン符号化'],
                    'ビット数': [total_bits_fixed, total_bits_huffman],
                    '効率性': [f'{bits_per_char_fixed} bits/文字', f'{total_bits_huffman/total_chars:.2f} bits/文字']
                })
                
                fig_comparison = px.bar(
                    comparison_data,
                    x='符号化方式',
                    y='ビット数',
                    title="符号化方式の比較",
                    color='符号化方式',
                    text='効率性'
                )
                fig_comparison.update_traces(textposition='outside')
                fig_comparison.update_layout(height=400)
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # 説明
                st.markdown(f"""
                ### 🎯 ハフマン符号化の効果
                
                - **固定長符号化**: 各文字を{bits_per_char_fixed}ビットで表現 → 合計{total_bits_fixed}ビット
                - **ハフマン符号化**: 頻度に応じて可変長で表現 → 合計{total_bits_huffman}ビット
                - **圧縮効果**: {compression_ratio:.1f}%のデータ量削減を実現！
                
                頻度の高い文字ほど短いビット列が割り当てられるため、全体のデータ量を効率的に削減できます。
                """)
    
    else:
        st.warning("⚠️ 正しいデータを入力してください（文字の重複なし、出現回数は正数）")
    
    # フッター
    st.markdown("---")
    st.markdown("""
    ### 💡 ハフマン符号化について
    
    ハフマン符号化は、データの出現頻度を利用した可変長符号化の手法です：
    - 📊 **頻度ベース**: よく出現する文字に短いビット列を割り当て
    - 🌳 **二分木構造**: 効率的な符号生成のためのツリー構造
    - 🔄 **最適性**: 与えられた頻度に対して最も効率的な符号を生成
    - 💾 **応用**: ZIP、JPEG、MP3など多くの圧縮形式で使用
    """)

if __name__ == "__main__":
    main()