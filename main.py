import requests


def test() -> None:
    url = "https://www.dirk.nl/boodschappen"
    data = requests.get(url)
    print(data)


def main() -> None:
    test()


if __name__ == "__main__":
    main()