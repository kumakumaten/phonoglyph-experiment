# phonoglyph_math.py
import numpy as np

# 日本語の統計的平均値（ベースライン）
BASELINE = {'vf': 16.6, 'vb': 34.3, 'obs': 24.7, 'son': 19.0, 'vd': 5.3}

def get_amplified_diff(val, baseline_key, amp_power=0.8):
    """
    ベースラインからの偏差を計算し、指定されたべき乗で非線形増幅する。
    """
    diff = val - BASELINE[baseline_key]
    return np.sign(diff) * (abs(diff) ** amp_power) * 1.2

def calculate_phonoglyph_coordinates(vf, vb, obs, son, vd, theta_points=3000, amp_power=0.8):
    """
    音素パラメータから直交座標系(x, y)と線幅(line_w)を計算して返す中核モジュール。
    """
    d_vf  = get_amplified_diff(vf, 'vf', amp_power)
    d_vb  = get_amplified_diff(vb, 'vb', amp_power)
    d_obs = get_amplified_diff(obs, 'obs', amp_power)
    d_son = get_amplified_diff(son, 'son', amp_power)
    
    # [CRITICAL FIX] 教授の指摘（学術的裏付けの欠如）を反映し、
    # 有声音(vd)によるパラメータ増幅処理を一時的に無効化。
    # d_vd  = get_amplified_diff(vd, 'vd', amp_power)

    theta = np.linspace(0, 2 * np.pi, theta_points)

    # 有機的形態の生成（トポロジー合成）
    r = 0.3 + (d_vb * 0.1)
    r += (0.4 + d_son) * np.cos(2 * theta)
    r += (0.3 + d_vf) * np.cos(3 * theta)
    
    spike_amp = max(0, 0.1 + d_obs * 0.5)
    r += spike_amp * np.cos(17 * theta)

    # トポロジー崩壊の防止（半径のマイナス反転をクリッピング）
    r = np.maximum(r, 0.05)

    # 直交座標への変換
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    # 心理物理学的なスケールの正規化（面積バイアスの排除）
    max_extent = np.max(np.sqrt(x**2 + y**2))
    if max_extent > 0:
        scale_factor = 0.9 / max_extent
        x = x * scale_factor
        y = y * scale_factor

    # [CRITICAL FIX] 線の太さの主観的変動を排除し、一律 1.5 に固定する
    line_w = 1.5

    return x, y, line_w