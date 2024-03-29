# Color Change Events
Terminal programs can query the terminal's colors by sending the color's corresponding `OSC` sequence with `?` instead of a color.

However, long lived programs currently have no way of being notified about changes to these colors.
This is particularly interesting in terminals that dynamically adapt to the OS's dark-light preference.

The goal is to extend terminals with *continous reporting* for each color.

## Syntax
The *OSC Color Control Sequences* are extended with two new special *spec* values analogous to the existing special *spec* `?`:

* `?+` enables continous reporting of the color set by the OSC sequence.
* `?-` disables continous reporting of the color set by the OSC sequence.

Each color in the 256-color table can have continous reporting enabled or disabled individually.

If the terminal supports querying / setting multiple colors in one sequence (e.g. `OSC 4 ; 0 ; red ; 1 ; ? ST` sets `0` to red and queries `1`) then this is also extended to enabling / disabling continous reporting (e.g. `OSC 4 ; 0 ; red ; 1 ; ? ; 2 ; ?- ; 3 ; ?+ ST` sets `0` to red, queries `1`, disables continous reporting for `2` and enables continous reporting for `3`).

*Special* colors i.e. colors set via `OSC 5` and the corresponding `OSC 4;256+x` alias are intentionally omitted from this specification.

## Reports
The terminal sends a report if and only if the *effective value* of a color changes and continous reporting is enabled for that color.

Continous reporting always produces OSC color control sequences in *canonical form*.

Upon enabling continous reporting, the current value is **not** reported. Programs that wish to know the current value send the sequence to enable continous reporting followed by the sequence for a one-time report. The reverse order is incorrect and may lead to a race condition.

## Effective Value
The *effective value* of a color is the value that would be reported by querying the terminal using a one-time query (`?`).

Some sources that may affect the *effective value*:
* The corresponding `OSC` color control sequence
* The corresponding `OSC` reset sequence
* User Preferences

This definition leaves room for terminals to change a color's value without affecting the *effective value* as long as the one-time query also doesn't report the change (e.g. slight darkening of the background of an unfocused pane).

Additionally this definition accounts for terminals that have multiple "levels" per color (e.g. user preference and set via `OSC` sequence).

## Canonical Form
An OSC color control sequence is in *canonical form* if:
* It uses the 7-bit `C1` encoding.
* It is terminated by `ST`.
* It uses the `rgb:rrrr/gggg/bbbb` form for colors without alpha and the `rgba:rrrr/gggg/bbbb/aaaa` form for colors with alpha. The channels are encoded as 16-bit hexadecimal numbers.

## Reset
Analogously to mouse reporting and FocusIn/FocusOut reporting, continous reporting is disabled when the terminal is reset using `DECSTR`, `DECSR`, or `RIS`.

## Partial Support
Terminals are still considered to conform to this spec if they omit continous reporting for colors that they don't support for setting / one-time querying.

## Implementation
* [VTE]: [issue][vte-issue] open, in discussion
* [Alacritty]: no issue opened yet
* [iTerm2]: no issue opened yet
* [tmux]: no issue opened yet
* [zellij]: no issue opened yet

Not on the list? Feel free to open a PR.

## Prior Art
### `SIGWINCH`
This mechanism is implemented by [iTerm][iterm-sigwinch].
Some tools such as [tmux][tmux-sigwinch] and [zellij][zellij-sigwinch] already interpret `SIGWINCH` as a color changed signal.

Using an escape sequence to deliver the change notification
has a couple of advantages over using `SIGWINCH`:

* `SIWGINCH` is fired many times when the terminal is resized.
  Applications that care about the color need to debounce the signal somehow
  to avoid sending `OSC 10` / `OSC 11` too often.
* An escape sequence can deliver the new color value
  directly so applications don't have to send `OSC 10` / `OSC 11`
  themselves.
* An escape sequences is portable to Windows.

## Possible Extensions
* Extend continous reporting to *special* colors (bold, ...).
* Shorthand for enabling continous reporting for all colors in the 256-color table simultaneously.

## Ⅰ. OSC Color Control Sequences
* `OSC 4`: 256-color palette
* (`OSC 5`: Special Color)
* `OSC 10`: VT100 text foreground color
* `OSC 11`: VT100 text background color
* `OSC 12`: text cursor color
* `OSC 13`: pointer foreground color
* `OSC 14`: pointer background color
* `OSC 15`: Tektronix foreground color
* `OSC 16`: Tektronix background color
* `OSC 17`: highlight background color
* `OSC 18`: Tektronix cursor color
* `OSC 19`: highlight foreground color

The colors set by `OSC 10` to `OSC 19` are referred to as *dynamic colors*.

Each of these colors has a corresponding reset sequence
`OSC 100+x`. So for example `OSC 13` is reset by `OSC 113`.

[source][xterm-ctrlseqs]

## Ⅱ. Terminal Survey
The following terminals do something when encountering the new sequences:
* rxvt-unicode: Sets background to pink because `?+` and `?-` are unrecognzied colors.
* Terminology: Reports the current color (It recognizes anything that starts with `?` as a one-time query).
* zellij: Reports the current color for `OSC 4` (It recognizes anything that starts with `?` as a one-time query).

The following terminals do nothing when encountering the new sequences:
* Alacritty
* Contour
* foot
* iTerm2
* JediTerm
* kitty
* Konsole
* Linux console
* mintty
* Rio
* st
* Terminal.app
* tmux
* vte
* WezTerm
* xterm
* xterm.js

Tested using [test.py](./test.py).

## Ⅲ. Additional Links
* [xterm's Control Sequences][xterm-ctrlseqs]
* [Kitty's Terminal Protocol Extensions](https://sw.kovidgoyal.net/kitty/protocol-extensions/)
* [WezTerm's Escape Sequences](https://wezfurlong.org/wezterm/escape-sequences.html)
* [iTerm2's Escape Sequences](https://iterm2.com/documentation-escape-codes.html)

[VTE]: https://gitlab.gnome.org/GNOME/vte
[vte-issue]: https://gitlab.gnome.org/GNOME/vte/-/issues/2740
[Konsole]: https://invent.kde.org/utilities/konsole
[tmux]: https://github.com/tmux/tmux
[zellij]: https://github.com/zellij-org/zellij
[Alacritty]: https://github.com/alacritty/alacritty
[iTerm2]: https://gitlab.com/gnachman/iterm2/-/issues
[iterm-sigwinch]: https://gitlab.com/gnachman/iterm2/-/issues/9855
[tmux-sigwinch]: https://github.com/tmux/tmux/issues/3582
[zellij-sigwinch]: https://github.com/zellij-org/zellij/pull/1358
[xterm-ctrlseqs]: https://invisible-island.net/xterm/ctlseqs/ctlseqs.txt
