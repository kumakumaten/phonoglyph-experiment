# phonoglyph_math.py
import numpy as np

# 日本語の統計的平均値（4分類）。
# ※旧5分類では濁音 g,z,d,b を "voiced(vd)" として別軸で集計していたが、
#   音声学的に g,z,d,b は阻害音(obstruent) である。よって obstruent に統合した。
#   これに伴い obstruent の基準値を「旧24.7 + 旧vd 5.3 = 30.0」に更新（vf/vb/son は据え置き）。
# 'vd' キーは旧コード・管理者シミュレーターとの互換のため残すが、図形計算では一切使用しない。
BASELINE = {'vf': 16.6, 'vb': 34.3, 'obs': 30.0, 'son': 19.0, 'vd': 5.3}

def calculate_phonoglyph_coordinates(vf, vb, obs, son, vd=0.0, theta_points=3000, amp_power=0.8):
    # vd（有声音）は4分類では obstruent に統合済み。互換のため引数は残すが図形計算には使用しない。
    def get_amp(val, baseline_key):
        diff = val - BASELINE[baseline_key]
        return np.sign(diff) * (abs(diff) ** amp_power) * 1.2

    d_vf  = get_amp(vf, 'vf')
    d_vb  = get_amp(vb, 'vb')
    d_obs = get_amp(obs, 'obs')
    d_son = get_amp(son, 'son')

    theta = np.linspace(0, 2 * np.pi, theta_points)

    # トポロジー合成
    r = 0.3 + (d_vb * 0.1)
    r += (0.4 + d_son) * np.cos(2 * theta)
    r += (0.3 + d_vf) * np.cos(3 * theta)

    spike_amp = max(0, 0.1 + d_obs * 0.5)
    r += spike_amp * np.cos(17 * theta)

    # 座標変換（rがマイナスの際の自己交差（鋭い棘）は許容する）
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    # 大きさの均一化（正規化）: 必ず枠内に収め、被験者が「大きさ」でなく「形状」で判断できるようにする
    max_extent = np.max(np.sqrt(x**2 + y**2))
    if max_extent > 0:
        scale_factor = 0.9 / max_extent
        x = x * scale_factor
        y = y * scale_factor

    # 線の太さは固定（濁音由来の交絡を排除）
    line_w = 1.5

    return x, y, line_w
