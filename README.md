# MindFlow

A modern, customizable mind mapping tool built with CustomTkinter for Python 3.12+.

## Features

- Clean, modern interface using CustomTkinter
- Create mind maps with a central topic
- Add child nodes with the Tab key
- Visual feedback for active nodes
- Automatic node positioning

## Installation

```bash
pip install mindflow
```

## Quick Start

```python
from mindflow import MindMap

app = MindMap()
app.mainloop()
```

## Usage

1. Run the application
2. A central node will appear
3. Press Tab to add child nodes to the active node
4. The active node is highlighted with a blue border

## Requirements

- Python 3.12 or higher
- CustomTkinter 5.2.0 or higher

## Development

To set up the development environment:

```bash
git clone https://github.com/pabloschaffner/mindflow.git
cd mindflow
pip install -r requirements.txt
```

## License

MIT License
