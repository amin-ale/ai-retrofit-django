from .config import get


def cost_usd(input_tokens, output_tokens):
    price_in = get("PRICE_INPUT_PER_MTOK")
    price_out = get("PRICE_OUTPUT_PER_MTOK")
    return (input_tokens * price_in + output_tokens * price_out) / 1_000_000
