# Color Change Events
Terminal programs can already query the terminal's colors by sending the color's corresponding `OSC` sequence with `?` instead of a color.

Long lived programs currently have no way of being notified of changes to these colors.
This is particularly interesting in terminals that dynamically adapt to the OS's dark-light preference.

The goal of this proposal is to extend terminals to continously report changes to their colors.
Programs can enable this by sending the color's corresponding `OSC` sequence with `?+` instead of a color and `?-` to disable reporting.

## Granularity
> TODO: Define the term *color* as used in spec to refer to a palette color (256) or to a *special* color. \
> TODO: Document that each color has its own subscription.
> TODO: Mention appendix with list of OSC sequences.

## Syntax
> TODO: Rework

For `OSC 4` the syntax is as follows: `OSC 4 ; c ; ?+ ST` and `OSC 4 ; c ; ?- ST` where `c` is a color index. \
For `OSC 1[1-9]` the syntax is as follows `OSC Ps ; ?+ ST` and `OSC Ps ; ?- ST` where `Ps` is one of `10, 11 ... 19`

If `?+` is given, then the terminal will reply with a control sequence of the same form which can be used to set the corresponding dynamic color every time that color is changed.

If `?-` is given, then the terminal will stop continuously reporting the corresponding dynamic color.

#### Remarks
1. `BEL` is also accepted in place of `ST`.
2. `OSC 4` accepts multiple color / spec pairs, naturally this extends to `?+` and `?-` as well.

## Reports
A report MUST be sent to applications if the *effective* color changes, that is if the corresponding one-time query would observe a different value. The continous query MUST report the same color as if the application queried using a one-time query in that moment. 

Terminals SHOULD not send a report if the effective color has not changed.
To avoid infinite loops between terminals and programs a report MUST NOT be sent if an OSC sequence sets the color to the already effective value.

In particular:
* If a terminal changes the color (e.g. slight darkening of the background of an unfocused pane)
  and doesn't report this using the one-time query then the color reported by the continous query doesn't report it either.
* Terminals that have multiple "levels" of colors (e.g. user preference and set via OSC) report the
  *effectively* used color value. If a color with lower priority is changed then the terminal may or may not report this as a change as long as it reports the *effective* color value.
* If the color is set via `OSC` to the same value it already has (either previosly set via OSC or by user preference) then
  terminals should not send a report.
* Upon enabling continous reporting, the current value is NOT reported. Programs that wish to know the current value send the sequence to enable continous reporting followed by the sequence for a one-time report. The reverse order is incorrect and may lead to a race condition.
* If an `OSC` reset sequence doesn't change the color because it already was reset then a report may or may not be sent.
* If an application sets a color using an OSC sequence for which it has continous reporting enabled, it also receives a report (given that the effective color was changed by the OSC sequence).
* > TODO: bold fg has an implicit dependency on fg, so if fg changes, bold fg needs to be reported as changed
* > OSC 106 (xterm: enable/disable a given special color; VTE: unsupported) should also report change. \
  > [Note about OSC 106 in xterm: while OSC 4, 5, 10..19 and their 100+ counterparts apply retroactively on previous contents, 106 does not, it only affects new output.]

## Canonical Form
An OSC color sequence is in *canonical form* if:
* It uses the 7-bit (`C1`) encoding.
* It is terminated by `ST`.
* It uses the `rgb:<r>/<g>/<b>` syntax for colors without alpha and the `rgba:<r>/<g>/<b>/<a>` syntax for colors with alpha channel. The channels are encoded as 16-bit hexadecimal colors.

> TODO: `OSC 4;256+x` is an alias for `OSC 5;x`


## Report Syntax
> TODO: reports always use the *canonical form* in terms of 
> * ST/BEL and C1/C0.
> * `OSC 4;256+x` is an alias for `OSC 5;x`
> * More?

## Disable Continous Reporting
> TODO

## Relation To One-Time Querying
Terminals MUST only implement continous querying for a color if the color also supports one-time querying.

## Implementation
* [VTE]: [issue][vte-issue] open, in discussion
* [Alacritty]: no issue opened yet
* [iTerm2]: no issue opened yet
* [tmux]: no issue opened yet
* [zellij]: no issue opened yet

Not on the list? Feel free to open a PR.

## Open Questions
* How should continous reporting interact with soft reset, hard reset, etc.
* > TODO: Reporting "bold color" (OSC 5;0) seems to be broken in both xterm and VTE if the said feature is disabled: #2768. Okay to leave it like that, and not detail in the spec what to do with this? Or should this new spec put pressure on terminals to fix one-off reporting too, to report the actual value?


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

## Ⅰ. OSC Sequences
> TODO: Extend this with OSC 4 / 5 and the corresponding reset sequences.
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

[source][xterm-ctrlseqs]

## Ⅱ. Terminal Survey
The following terminals were tested for their *current* behaviour when encountering `?+` and `?-` in place of `?`. The goal is to prevent the proposed syntax from interfering with current behaviour.

> TODO. Survey terminals listed here: https://github.com/bash/terminal-dark-light-agenda/tree/main/x11-colors

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
[xterm-ctrlseqs]: https://invisible-island.net/xterm/ctlseqs/ctlseqs.pdf
