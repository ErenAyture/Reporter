import numpy
import numbers

class RangeDict(dict):
    """
    Dictionary for interval keys. Supports open-ended ranges with '+' for +inf, '-' for -inf.
    Example: '-100:-20', '-:0', '0:100', '100:+'
    """

    def __getitem__(self, item):
        # ① recognise every real number – Python float/int AND NumPy scalars
        if isinstance(item, numbers.Real):          # <-- replace old line
            val = float(item)
            for key, colour in self.items():
                low_s, high_s = key.split(':')
                low  = float('-inf') if low_s.strip(' +').lower() in ('-', 'inf') else float(low_s)
                high = float('inf')  if high_s.strip(' +').lower() in ('+', 'inf') else float(high_s)
                if low <= val < high:               # use < high to avoid overlap
                    return colour
        # fallback – let dict raise if someone really indexes with the string
        return super().__getitem__(item)

    def get_range(self, item):
        # Same logic for descriptive ranges
        if isinstance(item, (float, int, numpy.floating)):
            val = float(item)
            for key in self:
                ran = key.split(":")
                if ran[0] == "-" or ran[0].lower() == "-inf":
                    low = "-∞"
                else:
                    low = ran[0]
                if ran[1] == "+" or ran[1].lower() == "+inf":
                    high = "+∞"
                else:
                    high = ran[1]
                if (float(low.replace("-∞","-1e30")) if low == "-∞" else float(low)) <= val <= (float(high.replace("+∞","1e30")) if high == "+∞" else float(high)):
                    return f"{low} to {high}"
        else:
            ran = item.split(":")
            low = "-∞" if ran[0] == "-" or ran[0].lower() == "-inf" else ran[0]
            high = "+∞" if ran[1] == "+" or ran[1].lower() == "+inf" else ran[1]
            return f"{low} to {high}"
        raise KeyError(item)


LTE_Ranges = {
    "rsrp": RangeDict({
        "-INF:-141": '#888888',      # Fallback (gray) for too low
        "-141:-120": '#e30000',
        "-120:-110": '#e13900',
        "-110:-100": '#ff7300',
        "-100:-95":  '#ffaa00',
        "-95:-90":   '#dfe300',
        "-90:-80":   '#aad500',
        "-80:-70":   '#71b800',
        "-70:-44":   '#008000',
        "-44:+INF":  '#888888',      # Fallback for too high (gray)
    }),
    "rsrq": RangeDict({
        "-INF:-20":  '#888888',      # Fallback (gray) for too low
        "-20:-18":   '#e13900',
        "-18:-12":   '#ff7300',
        "-12:-10":   '#ffaa00',
        "-10:-6":    '#aad500',
        "-6:-3":     '#008000',
        "-3:+INF":   '#888888',      # Fallback for too high
    }),
    "rssinr": RangeDict({
        "-INF:-20":  '#888888',      # Fallback for too low
        "-20:-10":   '#e30000',
        "-10:0":     '#ffaa00',
        "0:15":      '#dfe300',
        "15:25":     '#aad500',
        "25:35":     '#71b800',
        "35:50":     '#008000',
        "50:+INF":   '#888888',      # Fallback for too high
    }),
    "dl_throughput": RangeDict({
        "-INF:0":      '#888888',    # Fallback for too low
        "0:1000":      '#e30000',
        "1000:3000":   '#ffaa00',
        "3000:5000":   '#dfe300',
        "5000:10000":  '#71b800',
        "10000:+INF":  '#008000',
    }),
    "ul_throughput_mb": RangeDict({
        "-INF:0":      '#888888',    # Fallback for too low
        "0:1000":      '#e30000',
        "1000:3000":   '#ffaa00',
        "3000:5000":   '#dfe300',
        "5000:10000":  '#71b800',
        "10000:+INF":  '#008000',
    }),
}

# ── self-test -- run “python RangeDict.py” ───────────────────
# if __name__ == "__main__":
#     from RangeDict import LTE_Ranges
#     import numpy as np
#     print(LTE_Ranges["rsrp"][-165])            # → '#71b800' (or whatever colour you set)
#     print(LTE_Ranges["rsrp"][np.int64(-65)])  # should print the SAME colour
