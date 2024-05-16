# Unsolicited Reporting (of Colors)

### Summary
This specification introduces an opt-in mechanism for terminals to inform applications of individual changes to the color palette (background, foreground, etc.). This is done by augmenting the behaviour of the existing `OSC` color queries using a new DEC private mode.

### Motivation
Applications today can query the terminal's colors using XTerm's `OSC 4`, `OSC 5`, `OSC 10`, ... sequences. There is however no way to be informed when these color change.

This can happen when the user changes their color scheme manually or when the terminal changes with the system's dark-light preference.

The current state is an issue for the following kinds of applications:
* **multiplexers** such as tmux need to respond to one-time queries and have no way of knowing when the connected terminal changes its colors.
* **TUIs** such as VIM only detect the users dark-light preference on startup and don't change with the terminal.

## Overview
Terminals send an *unsolicited report* when the *effective value* of a *tracked query* changes.

Applications opt in to this behaviour by enabling the new *Unsolicited Reports Mode*. One-time queries sent while this mode is enabled add the query to the terminal's set of *tracked queries*. The one-time report is still generated and follows the same principles as unsolicited reports with regards to its format.

This design has nice consequence for backwards compatibility: Apps send `DECSET 2510` followed by the query sequence. In terminals that don't support this specification they at least get back a one-time response.

Unsolicited reporting follows the granularity of the queries themselves. This means that individual colors of the 256-color palette can be tracked by sending an `OSC 4` query while the *unsolicited reports mode* is enabled.

## Definitions

### Unsolicited Reports Mode
Unsolicited Reports Mode is a new DEC private mode.
It uses the `DECSET`/`DECRST` number `2510` [^1].

**Set**ting the mode using `DECSET` doesn't have an immediate effect. \
One-time queries received while the mode is enabled add the query to the set of *tracked queries*.

**Reset**ting the mode either indirectly or using `DECRST` will \
clear the set of *tracked queries*.

While the mode initially only affects *OSC color queries* it is intentionally kept general to allow future extensions. For example unsolicited reports for `CSI ... t` window ops.

<small>

[^1]: I chose this number to be close to the existing numbers chosen by VTE but not conflict with any existing `DECSET` numbers. See my [exhaustive list][dec-modes] of DEC modes.

</small>

### Tracked Queries
The set of tracked queries determines for which changes the terminal generates an *unsolicited* report. Queries can be added to this set by sending a one-time query while the *unsolicited reports mode* is enabled.

### Unsolicited Report
Terminals send an *unsolicited report* when the *effective value* of a *tracked query* changes.

Unsolicited reports always use the *canonical form* if the original query was in canonical form. If the original query is not in canonical form it is left undefined what form the report uses.

Terminals may report a change even if the *effective value* has not changed. \
Programs that have continuous reporting enabled *and* want to use an OSC sequence
to set the queried value have to be careful to avoid a feedback loop.

Terminals may choose to bundle up reports (e.g. to avoid reporting multiple changes in quick succession) and deliver them with a short delay.
Reports are emitted in the same order as the changes have occurred in. When multiple changes occur in one bundling interval the order is determined by the first change.

### Effective Value
The *effective value* of a palette color is the value reported in response to a one-time `OSC` query (e.g. `OSC 11 ; ?`).

Some sources that may affect the *effective value*:
* The corresponding `OSC` color control sequence
* The corresponding `OSC` reset sequence
* User Preferences

This definition leaves room for terminals to change a color's value without affecting the *effective value* as long as the one-time query also doesn't report the change (e.g. slight darkening of the background of an unfocused pane).

Additionally this definition accounts for terminals that have multiple "levels" per color (e.g. user preference and set via `OSC` sequence).

### Canonical Form
An `OSC` color control sequence is in *canonical form* if:
* It is terminated by `ST` (instead of `BEL`).
* It is encoded as `C0`.
* It uses the `rgb:rrrr/gggg/bbbb` form for fully opaque colors and the `rgba:rrrr/gggg/bbbb/aaaa` form for partially opaque colors. The channels (and opacity) are encoded as 16-bit hexadecimal numbers.

For *special colors* the canonical form is `OSC 5 ; n` instead of `OSC 4 ; 256+n`.

> ℹ️ Applications that want to be compatible with a wide range of terminals have to support some variation in the responses:
> * Both `st` and macOS' built-in terminal always terminate their response with `BEL`.
> * `urxvt`'s current version terminates responses with `ESC` if the query uses `ST` ([fixed](http://cvs.schmorp.de/rxvt-unicode/src/command.C?revision=1.600&view=markup)). 
> * Terminology's current version uses the `#rrggbb` format when responding to `OSC 10` queries ([fixed](https://git.enlightenment.org/enlightenment/terminology/issues/14)).
> * iTerm2 [can be configured](https://gitlab.com/gnachman/iterm2/-/commit/5c5785f3632b8e90dd69f458411a8b8b17aa0599) to use 8-bit color components instead of 16-bit.

### OSC Color Control Sequence
*These definitions are mostly taken from the [XTerm Control Sequences] document.*

An `OSC` color control sequence is one of the following `OSC` sequences:
* `OSC 4 ; n`: 256-color palette color
* `OSC 5 ; n`: Special color
* `OSC 10`: VT100 text foreground color
* `OSC 11`: VT100 text background color
* `OSC 12`: Text cursor color
* `OSC 13`: Pointer foreground color
* `OSC 14`: Pointer background color
* `OSC 15`: Tektronix foreground color
* `OSC 16`: Tektronix background color
* `OSC 17`: Highlight background color
* `OSC 18`: Tektronix cursor color
* `OSC 19`: Highlight foreground color

The colors set by `OSC 10` to `OSC 19` are referred to as *dynamic colors*.

Each of these colors has a corresponding reset sequence
`OSC 100+x`. For example `OSC 13` is reset by `OSC 113`.

## Prior Art and Alternatives

<details>

### `SIGWINCH`
This mechanism is implemented by [iTerm2][iterm-sigwinch].
Some tools such as [tmux][tmux-sigwinch] and [zellij][zellij-sigwinch] already interpret `SIGWINCH` as a color changed signal.

Using an escape sequence to deliver the change notification
has a couple of advantages over using `SIGWINCH`:

* `SIWGINCH` is fired many times when the terminal is resized.
  Programs that care about the color need to debounce the signal somehow
  to avoid sending `OSC 10` / `OSC 11` too often.
* There's a clear and granular opt-in for color notification
  so programs can choose which colors they care about.
* An escape sequence can deliver the new color value
  directly so programs don't have to send `OSC 10` / `OSC 11`
  themselves.
* An escape sequences is portable to situations without side-channel (e.g. Windows or plain Telnet).

### Dark and Light Mode Detection
Contour provides [dark and light mode detection][contour-dark-light] using a custom device status report sequence.

This is not sufficient for multiplexers that want to respond to one-time OSC color queries with up-to-date values.

### Extend OSC Queries with `+?` and `-?`
See the [discussion][vte-discussion] in VTE's issue tracker.

### Colour Table Report
See the [discussion][vte-discussion] in VTE's issue tracker.

</details>

## Resources

* [XTerm Control Sequences]
* [Tau's Exhaustive List of DEC Modes][dec-modes]
* [Kitty's Terminal Protocol Extensions](https://sw.kovidgoyal.net/kitty/protocol-extensions/)
* [WezTerm's Escape Sequences](https://wezfurlong.org/wezterm/escape-sequences.html)
* [iTerm2's Escape Sequences](https://iterm2.com/documentation-escape-codes.html)
* [Contour's VT extensions][contour-vt-ext]
* [mintty's Control Sequences][mintty-ctrlseqs]
* [`console_codes(4)` man page][linux-console-codes]


[vte-discussion]: https://gitlab.gnome.org/GNOME/vte/-/issues/2740
[XTerm Control Sequences]: https://www.invisible-island.net/xterm/ctlseqs/ctlseqs.html
[iterm-sigwinch]: https://gitlab.com/gnachman/iterm2/-/issues/9855
[tmux-sigwinch]: https://github.com/tmux/tmux/issues/3582
[zellij-sigwinch]: https://github.com/zellij-org/zellij/pull/1358
[contour-vt-ext]: http://contour-terminal.org/vt-extensions
[contour-dark-light]: http://contour-terminal.org/vt-extensions/color-palette-update-notifications/
[mintty-ctrlseqs]: https://github.com/mintty/mintty/wiki/CtrlSeqs
[linux-console-codes]: https://man7.org/linux/man-pages/man4/console_codes.4.html
[dec-modes]: https://tau.garden/dec-modes/
