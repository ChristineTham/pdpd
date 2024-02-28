import sys

def parse_into_words(filename):
    with open(filename, 'r') as file:
        data = file.read()
        words = data.split()
        return words

def main():
    if len(sys.argv) != 2:
        print("Usage: python <script.py> <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    words = parse_into_words(filename)
    print(words)

if __name__ == "__main__":
    main()
