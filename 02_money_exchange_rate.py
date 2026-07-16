import json
import time
import urllib.error
import urllib.request

CURRENCIES = {
    "1": ("USD", "미국 달러"),
    "2": ("JPY", "일본 엔"),
    "3": ("CNY", "중국 위안"),
}
API_URL = "https://open.er-api.com/v6/latest"
SUCCESS_REFRESH_SECONDS = 30
FAILURE_RETRY_SECONDS = 3


def fetch_exchange_rate(base: str, symbol: str) -> float:
    url = f"{API_URL}/{base}"
    with urllib.request.urlopen(url, timeout=10) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    if data.get("result") != "success":
        raise RuntimeError("환율 정보를 가져오지 못했습니다.")

    rates = data.get("rates", {})
    if symbol not in rates:
        raise RuntimeError(f"서버 응답에 {symbol} 환율이 없습니다.")

    return float(rates[symbol])


def select_currency() -> tuple[str, str]:
    print("환율 확인 대상 통화를 선택하세요.")
    for key, (_, name) in CURRENCIES.items():
        print(f"{key}. {name}")

    while True:
        choice = input("번호를 입력하세요 (1-3): ").strip()
        if choice in CURRENCIES:
            return CURRENCIES[choice]
        print("올바른 번호를 입력해 주세요.")


def format_krw_rate(rate: float, currency_name: str, currency_code: str) -> str:
    inverse = 1 / rate if rate != 0 else 0
    return (
        f"1 KRW = {rate:,.6f} {currency_code} ({currency_name})\n"
        f"1 {currency_code} = {inverse:,.2f} KRW"
    )


def main() -> None:
    print("실시간 환율 확인 터미널 앱")
    print("1부터 100까지 숫자 선택 기능이 아닌 환율 조회 앱입니다.")
    print("Ctrl+C를 눌러 종료할 수 있습니다.\n")

    currency_code, currency_name = select_currency()
    print(f"선택한 통화: {currency_name} ({currency_code})\n")

    try:
        while True:
            try:
                rate = fetch_exchange_rate("KRW", currency_code)
                print("='" * 20)
                print(time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime()))
                print(format_krw_rate(rate, currency_name, currency_code))
                print(f"{SUCCESS_REFRESH_SECONDS}초 후에 다시 확인합니다...\n")
                time.sleep(SUCCESS_REFRESH_SECONDS)
            except (urllib.error.URLError, RuntimeError) as exc:
                print("환율 정보를 가져오지 못했습니다:", exc)
                print(f"{FAILURE_RETRY_SECONDS}초 후에 다시 시도합니다...\n")
                time.sleep(FAILURE_RETRY_SECONDS)
    except KeyboardInterrupt:
        print("\n환율 조회 앱을 종료합니다.")


if __name__ == "__main__":
    main()
