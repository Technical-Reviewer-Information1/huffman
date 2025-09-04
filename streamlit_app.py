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
    
    def compress_text(self, text: str) -> str:
        """テキストをハフマン符号化で圧縮"""
        if not self.codes:
            return ""
        
        compressed = ""
        for char in text:
            if char in self.codes:
                compressed += self.codes[char]
            else:
                # 未知の文字の場合はそのまま追加（またはエラー処理）
                st.warning(f"文字 '{char}' はハフマン木に含まれていません")
        
        return compressed
    
    def decompress_text(self, compressed_text: str) -> str:
        """圧縮されたビット列をデコード"""
        if not self.root or not compressed_text:
            return ""
        
        decoded = ""
        current_node = self.root
        
        for bit in compressed_text:
            if bit == '0':
                current_node = current_node.left
            elif bit == '1':
                current_node = current_node.right
            else:
                continue
            
            # 葉ノードに到達した場合
            if current_node and current_node.char:
                decoded += current_node.char
                current_node = self.root
        
        return decoded

def calculate_frequency(text: str) -> Dict[str, int]:
    """テキストから文字頻度を計算"""
    frequency = {}
    for char in text:
        frequency[char] = frequency.get(char, 0) + 1
    return frequency

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
    
    # より良い間隔でノードを配置
    def calculate_positions(node, x=0.5, y=0.95, width=0.45, depth=0):
        if not node:
            return
        
        positions[node.id] = (x, y)
        
        if node.left or node.right:
            # 縦の間隔を広く取る
            vertical_spacing = 0.18
            if node.left:
                calculate_positions(node.left, x - width/2, y - vertical_spacing, width/2, depth + 1)
            if node.right:
                calculate_positions(node.right, x + width/2, y - vertical_spacing, width/2, depth + 1)
    
    calculate_positions(root)
    
    # ノードの描画
    def draw_nodes(node):
        if not node:
            return
        
        x, y = positions[node.id]
        
        if node.char:  # 葉ノード
            color = '#FFB6C1'  # ライトピンク
            border_color = '#FF1493'  # ディープピンク
            # 文字コードを大きく表示
            text = f"<b>{node.char}</b><br>頻度: {node.freq}<br><b>符号: '{codes[node.char]}'</b>"
            size = 100  # 80から100に拡大
        else:  # 内部ノード
            color = '#87CEEB'  # スカイブルー
            border_color = '#4169E1'  # ロイヤルブルー
            text = f"<b>合計: {node.freq}</b>"
            size = 90  # 70から90に拡大
        
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=size, color=color, line=dict(width=3, color=border_color)),
            text=text,
            textposition="middle center",
            textfont=dict(size=14, color='black'),  # フォントサイズを14に拡大、色を明示的に黒に指定
            showlegend=False
        ))
        
        # 子ノードへの線 - より太く目立つように
        if node.left:
            left_x, left_y = positions[node.left.id]
            fig.add_shape(type="line", x0=x, y0=y, x1=left_x, y1=left_y,
                         line=dict(color="#2F4F4F", width=4))  # 濃いグレー、太い線
            # "0"ラベルを大きく明確に
            mid_x, mid_y = (x + left_x) / 2, (y + left_y) / 2
            fig.add_annotation(
                x=mid_x-0.03, y=mid_y+0.03, 
                text="<b>0</b>", 
                showarrow=False,
                font=dict(size=18, color="red"),
                bgcolor="white",
                bordercolor="red",
                borderwidth=2
            )
        
        if node.right:
            right_x, right_y = positions[node.right.id]
            fig.add_shape(type="line", x0=x, y0=y, x1=right_x, y1=right_y,
                         line=dict(color="#2F4F4F", width=4))  # 濃いグレー、太い線
            # "1"ラベルを大きく明確に
            mid_x, mid_y = (x + right_x) / 2, (y + right_y) / 2
            fig.add_annotation(
                x=mid_x+0.03, y=mid_y+0.03, 
                text="<b>1</b>", 
                showarrow=False,
                font=dict(size=18, color="blue"),
                bgcolor="white",
                bordercolor="blue",
                borderwidth=2
            )
        
        draw_nodes(node.left)
        draw_nodes(node.right)
    
    draw_nodes(root)
    
    fig.update_layout(
        width=1000, height=700,  # サイズを大きく
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.1, 1.1]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 1]),
        title="<b>完成したハフマン木</b><br><span style='color:red'>赤: 左の子(0)</span> | <span style='color:blue'>青: 右の子(1)</span>",
        title_x=0.5,
        title_font_size=16,
        plot_bgcolor='white',
        paper_bgcolor='#F8F9FA'  # 薄いグレー背景
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
    
    # モード選択
    st.header("🎯 学習モードを選択")
    mode = st.radio(
        "どちらの方法で学習しますか？",
        ["📝 文字列から自動で頻度計算", "✏️ 手動で文字と頻度を入力"],
        horizontal=True
    )
    
    if mode == "📝 文字列から自動で頻度計算":
        # 文字列入力モード
        st.header("📝 文字列圧縮モード")
        st.write("圧縮したいテキストを入力してください：")
        
        col_text1, col_text2 = st.columns([3, 2])
        
        with col_text1:
            # セッション状態でテキストを管理
            if 'sample_text' not in st.session_state:
                st.session_state.sample_text = "HELLO WORLD"
            
            # サンプルテキストボタン
            col_sample1, col_sample2, col_sample3 = st.columns(3)
            with col_sample1:
                if st.button("📚 サンプル1"):
                    st.session_state.sample_text = "ABRACADABRA"
                    # ハフマン木をリセット
                    st.session_state.tree_built = False
                    st.session_state.huffman = HuffmanCoding()
                    st.rerun()
            with col_sample2:
                if st.button("📚 サンプル2"): 
                    st.session_state.sample_text = "こんにちは世界"
                    # ハフマン木をリセット
                    st.session_state.tree_built = False
                    st.session_state.huffman = HuffmanCoding()
                    st.rerun()
            with col_sample3:
                if st.button("📚 サンプル3"):
                    st.session_state.sample_text = "AAAAABBBBCCCDDE"
                    # ハフマン木をリセット
                    st.session_state.tree_built = False
                    st.session_state.huffman = HuffmanCoding()
                    st.rerun()
            
            input_text = st.text_area(
                "圧縮するテキスト",
                value=st.session_state.sample_text,
                height=100,
                help="任意のテキストを入力してください"
            )
            
            # テキストが変更された場合はハフマン木をリセット
            if input_text != st.session_state.sample_text:
                st.session_state.sample_text = input_text
                st.session_state.tree_built = False
                st.session_state.huffman = HuffmanCoding()
        
        with col_text2:
            if input_text:
                # 文字頻度の自動計算と表示
                frequency_dict = calculate_frequency(input_text)
                freq_df = pd.DataFrame([
                    {"文字": char, "出現回数": freq, "割合(%)": f"{freq/len(input_text)*100:.1f}"}
                    for char, freq in frequency_dict.items()
                ])
                
                st.subheader("📊 文字頻度分析")
                st.dataframe(freq_df, use_container_width=True)
                
                # 頻度グラフ
                fig_freq = px.bar(
                    freq_df, x='文字', y='出現回数',
                    title="文字の出現頻度",
                    color='出現回数',
                    color_continuous_scale='viridis'
                )
                fig_freq.update_layout(height=300)
                st.plotly_chart(fig_freq, use_container_width=True)
        
        # 以降の処理で使用するために頻度辞書を設定
        if input_text:
            frequency_dict = calculate_frequency(input_text)
            # 入力テキストをセッション状態に保存
            st.session_state.input_text = input_text
    
    else:
        # 手動入力モード
        st.session_state.input_text = None  # テキストモードを無効化
        
        # 1. データ入力セクション
        st.header("📊 1. データ（文字と頻度）の入力")
        st.write("文字とその出現回数を入力してください：")
    
    if mode == "✏️ 手動で文字と頻度を入力":
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
        else:
            frequency_dict = None
    
    # 両方のモードで共通の処理
    if (mode == "📝 文字列から自動で頻度計算" and input_text) or (mode == "✏️ 手動で文字と頻度を入力" and frequency_dict):
        
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
                
                # 4. テキスト圧縮デモンストレーション（文字列モードの場合）
                if mode == "📝 文字列から自動で頻度計算" and hasattr(st.session_state, 'input_text') and st.session_state.input_text:
                    st.header("🗜️ 4. テキスト圧縮デモンストレーション")
                    
                    # 圧縮実行
                    original_text = st.session_state.input_text
                    compressed_binary = st.session_state.huffman.compress_text(original_text)
                    
                    if compressed_binary:
                        # 圧縮結果の表示
                        col_compress1, col_compress2 = st.columns(2)
                        
                        with col_compress1:
                            st.subheader("📝 元のテキスト")
                            st.code(original_text, language=None)
                            
                            st.subheader("🔢 圧縮後（バイナリ）")
                            # 長いバイナリ文字列を見やすく改行
                            binary_display = ""
                            for i in range(0, len(compressed_binary), 40):
                                binary_display += compressed_binary[i:i+40] + "\n"
                            st.code(binary_display, language=None)
                        
                        with col_compress2:
                            # 詳細統計
                            original_size_bits = len(original_text) * 8  # ASCII文字として8ビット/文字
                            compressed_size_bits = len(compressed_binary)
                            compression_ratio = (1 - compressed_size_bits / original_size_bits) * 100
                            
                            st.subheader("📊 圧縮統計")
                            
                            metrics_data = pd.DataFrame([
                                {"項目": "元のテキスト文字数", "値": f"{len(original_text)} 文字"},
                                {"項目": "元のサイズ（ASCII 8bit）", "値": f"{original_size_bits} bits"},
                                {"項目": "ハフマン符号ビット数", "値": f"{compressed_size_bits} bits"},
                                {"項目": "圧縮率", "値": f"{compression_ratio:.1f}%"},
                                {"項目": "サイズ削減", "値": f"{original_size_bits - compressed_size_bits} bits"}
                            ])
                            
                            st.dataframe(metrics_data, use_container_width=True, hide_index=True)
                            
                            # 圧縮効果の可視化
                            fig_compression = go.Figure(data=[
                                go.Bar(name='元のサイズ', x=['データサイズ'], y=[original_size_bits], 
                                       marker_color='lightcoral'),
                                go.Bar(name='圧縮後サイズ', x=['データサイズ'], y=[compressed_size_bits], 
                                       marker_color='lightgreen')
                            ])
                            fig_compression.update_layout(
                                title="圧縮効果の比較",
                                barmode='group',
                                yaxis_title="ビット数",
                                height=300
                            )
                            st.plotly_chart(fig_compression, use_container_width=True)
                        
                        # 展開テスト
                        st.subheader("🔄 展開テスト")
                        decompressed_text = st.session_state.huffman.decompress_text(compressed_binary)
                        
                        col_decomp1, col_decomp2 = st.columns(2)
                        with col_decomp1:
                            st.write("**元のテキスト:**")
                            st.code(original_text, language=None)
                        
                        with col_decomp2:
                            st.write("**展開されたテキスト:**")
                            st.code(decompressed_text, language=None)
                        
                        # 正確性チェック
                        if original_text == decompressed_text:
                            st.success("✅ 展開成功！元のテキストと完全に一致しています。")
                        else:
                            st.error("❌ 展開エラー！元のテキストと一致しません。")
                        
                        # インタラクティブな文字列テスト
                        st.subheader("🎮 インタラクティブ圧縮テスト")
                        test_text = st.text_input(
                            "任意のテキストを圧縮してみよう：",
                            value="TEST",
                            help="学習済みの文字のみ使用してください"
                        )
                        
                        if test_text and st.button("🗜️ 圧縮実行"):
                            test_compressed = st.session_state.huffman.compress_text(test_text)
                            test_decompressed = st.session_state.huffman.decompress_text(test_compressed)
                            
                            col_test1, col_test2, col_test3 = st.columns(3)
                            
                            with col_test1:
                                st.write("**入力:**")
                                st.code(test_text, language=None)
                            
                            with col_test2:
                                st.write("**圧縮結果:**")
                                st.code(test_compressed, language=None)
                            
                            with col_test3:
                                st.write("**展開結果:**")
                                st.code(test_decompressed, language=None)
                                
                                if test_text == test_decompressed:
                                    st.success("✅ 成功")
                                else:
                                    st.error("❌ 失敗")
    
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