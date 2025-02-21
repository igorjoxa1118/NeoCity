from rich.console import Console

console = Console()
console.print(
f"""
 Normal Foreground Text
[black] Normal Black Text [/black]
[bright_black] Bright Black Text [/bright_black]
[white] Normal White Text [/white]
[bright_white] Bright White Text [/bright_white]
[red] Normal Red Text [/red]      [bright_red] Bright Red Text [/bright_red]
[green] Normal Green Text [/green]    [bright_green] Bright Green Text [/bright_green]
[yellow] Normal Yellow Text [/yellow]   [bright_yellow] Bright Yellow Text [/bright_yellow]
[blue] Normal Blue Text [/blue]     [bright_blue] Bright Blue Text [/bright_blue]
[magenta] Normal Magenta Text [/magenta]  [bright_magenta] Bright Magenta Text [/bright_magenta]
[cyan] Normal Cyan Text [/cyan]     [bright_cyan] Bright Cyan Text [/bright_cyan]

  [white]1[/white] [bright_red]#include[/bright_red] [bright_white]<[bright_yellow]stdio.h[/bright_yellow]>[/bright_white]
  [white]2[/white] [bright_cyan]int[/bright_cyan] [bright_blue]main[/bright_blue][bright_white]()[/bright_white] {{
  [white]3[/white]    [bright_black]// printf() displays the string inside quotation[/bright_black]
[on black]  [white]4[/white]    [bright_blue]printf[/bright_blue][bright_white]([bright_green]\"Hello, World!\"[/bright_green])[/bright_white];                                             [/on black]
  [white]5[/white]    [bright_cyan]return[/bright_cyan] [bright_magenta]0[/bright_magenta];
  [white]6[/white] }}
"""[1:-1],
highlight = False
)
