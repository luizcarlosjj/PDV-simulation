# PDV Simples

Sistema de Ponto de Venda (PDV) simples em Python puro, com interface
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) e
banco de dados SQLite — pronto para gerar um único executável `.exe`.

## Funcionalidades

- **Venda**: leitura por código, busca de produto, múltiplos itens, atalho `F9` para fechar.
- **Produtos**: cadastro, edição, exclusão e busca.
- **Estoque**: posição atual, movimentações (entrada/saída/ajuste) e histórico.
- **Cupom não fiscal**: gerado ao finalizar — exibido em tela, salvo em `recibos/*.txt` e enviado para a impressora padrão.
- **Histórico de vendas**: filtro por período e reimpressão de cupons.
- **Relatórios**: total vendido, vendas por forma de pagamento e top 10 produtos.
- **Formas de pagamento**: Dinheiro (com cálculo de troco), Cartão Débito, Cartão Crédito e PIX.

## Estrutura

```
PDV-simulation/
├── main.py                # Entrada do programa
├── database.py            # Acesso ao SQLite
├── ui/                    # Telas (CustomTkinter)
│   ├── sale_screen.py
│   ├── products_screen.py
│   ├── stock_screen.py
│   ├── history_screen.py
│   ├── report_screen.py
│   └── receipt_window.py
├── utils/
│   ├── helpers.py         # Formatação BRL e parse decimal
│   └── receipt.py         # Geração / salvamento / impressão do cupom
├── recibos/               # Cupons em .txt (gerados em runtime)
├── requirements.txt
├── build.bat              # Script PyInstaller (Windows)
└── pdv.db                 # Banco SQLite (gerado no 1º uso)
```

## Como rodar (desenvolvimento)

```powershell
pip install -r requirements.txt
python main.py
```

O banco `pdv.db` é criado automaticamente na primeira execução.

## Gerar executável (.exe)

No Windows, com Python e dependências instaladas:

```powershell
build.bat
```

O arquivo será gerado em `dist\PDV-Simples.exe`. Distribua o `.exe`
junto com a pasta `recibos\` (ou ela será criada ao lado do executável
no primeiro uso).

## Atalhos

| Tecla | Ação                          |
|-------|-------------------------------|
| F9    | Finalizar venda               |
| Enter | Adicionar item (na tela Venda)|
