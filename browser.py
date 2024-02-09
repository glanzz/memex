from app.memex import Memex
if __name__ == "__main__":
  import sys
  memex = Memex()
  memex.load(sys.argv[1] if len(sys.argv) > 1 else None)
