# phonoglyph_math.py
import numpy as np

# 日本語の統計的平均値
BASELINE = {'vf': 16.6, 'vb': 34.3, 'obs': 24.7, 'son': 19.0, 'vd': 5.3}

def calculate_phonoglyph_coordinates(vf, vb, obs, son, vd, theta_points=3000, amp_power=0.8):
    def get_amp(val, baseline_key):
        diff = val - BASELINE[baseline_key]
        return np.sign(diff) * (abs(diff) ** amp_power) * 1.2

    d_vf  = get_amp(vf, 'vf')
    d_vb  = get_amp(vb, 'vb')
    d_obs = get_amp(obs, 'obs')
    d_son = get_amp(son, 'son')
    # 有声音(vd)の増幅は、線の太さを固定するため使用しない

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

    # ==========================================
    # 🛡️ 学術的統制（君の提案の具現化）
    # ==========================================
    
    # 1. 大きさの均一化（正規化）
    # どんなに棘が暴れても、必ず [-1, 1] の枠内に完璧に収める。
    # これにより被験者は「大きさ」に惑わされず「形状」だけで判断できる。
    max_extent = np.max(np.sqrt(x**2 + y**2))
    if max_extent > 0:
        scale_factor = 0.9 / max_extent
        x = x * scale_factor
        y = y * scale_factor

    # 2. 線の太さの排除（主観の排除）
    # 濁音による線の太さの変化を切り捨て、すべて 1.5 に固定する。
    line_w = 1.5

    return x, y, line_w