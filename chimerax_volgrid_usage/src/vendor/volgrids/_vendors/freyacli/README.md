# FREYA CLI
**Freya CLI** (FRamEwork for pYthon Applications) is, as the name suggests, a Python framework for building Command Line Interface (CLI) applications. It allows developers to use a set of well defined rules and specifications for the intended usage of the CLI (via the `FYR` format), while giving an intuitive idea to the users on what the app's CLI expects to receive.

As a bonus, **Freya CLI** provides a simple utility for coloring any printed text, via the `freyacli.Color` class. The colors provided are black, white, red, green, blue, yellow, magenta, cyan; with their respective *bright* variations, for a total of 16 colors.

## FYR / FYH format
- `FYR` (FreYa Rules) specifies a list of **rules** that must be followed when using an application's CLI. These rules are organized inside a hierarchy structure composed of **subcommand** nodes.
- `FYH` (FreYa Helps) should follow the same structure as its respective `FYR`. Instead of specifying the CLI rules, it stores the application-specific help descriptions that will be displayed whenever an incorrect use of the CLI is detected. These descriptions are automatically gathered by freya when producing the **help string**.

Below is an explanation of the argument **rules** and the **subcommand** nodes.

### Argument Rules
Argument rules specify how the arguments should be passed to the CLI and are specified in the `FYR` format. The simplest rule has the form:
```
name[]1.STR
```
where `name` is both the name that will be used to fetch the user values, and the name displayed in the automatic help string. The empty brackets represent that this argument is **positional** (e.g. like how the argument is passed to the command `cat README.md`). The expected type is passed after a `.`, in this case `STR` (`1` indicates that one value is expected, more on that [later](#argument-count)). Supported types are:
- `STR`: string
- `PATH`: a valid path (will be stored as a Python `Path` instance)
- `INT`: integer
- `FLOAT`: float


If the argument is intended to be a simple on/off flag instead (e.g. `-a` in `ls -a`), it would instead look like
```
name[a,all]
```

This means that the flag `name` can be toggled on by passing either the flag `-a` (short name) or `--all` (long name). Short names can only be 1-character long; numbers are currently not allowed. If only a short name is to be defined, you can write it as `[a,]`; if only a long name is needed instead, it can be written as `[,all]`.

Naturally, toggle flags should be optional by nature. To indicate that an argument is **optional**, a `~` char should be placed before the name. This applies to any kind of argument, be it positional or flag. So the previous example would be:

```
~name[a,all]
```

Flags can also have a value attached to them. It will look similar to the positional argument syntax, with the extra short/long flag names inside the brackets, e.g.:
```
~path_file[i,input]1.PATH
```

Finally, default values can be specified inside the `FYR` too. These will be assigned to optional arguments that the user didn't specify. It uses a `=` at the end of the rule (limitation: spaces are not allowed inside default values), e.g.:
```
~path_file[i,input]1.PATH=README.md
```

#### Argument Count
The number after the square brackets indicate how many values are expected for a given argument. Flags that take no arguments (i.e. toggle flags) must keep everything empty after the square brackets.

Futhermore, a `?` sign after the number represents arguments that could *optionally* take that amount of values, or none (inspired by regex notation). Note that this is not the same as *optional arguments*, but rather more specifically affects flags that can optionally be toggles **or** accept values. Avoid it for positional values:
```
# positional[]4?.INT # BAD:  avoid this syntax for positionals, it doesn't make sense that a positional can take 0 values
~positional[]4.INT   # GOOD: this is the proper way for optional positionals, as seen earlier
```
Do note the distinction when it corresponds to flags:

```
name[f,flag]2.INT   # (rare) this is a mandatory flag with 2 mandatory expect values
~name[f,flag]2.INT  # this is an optional flag. When used, 2 values MUST be provided
~name[f,flag]2?.INT # this is an optional flag. When used, 2 values COULD be provided
name[f,flag]2?.INT  # BAD: a mandatory flag shouldn't be able to receive 0 values (it defeats the purpose of the flag)
```

For a real life example of this kind of flags, see the description for `git`'s `--exec-path` flag in `man git`. Using the flag is optional; then, if you do use the flag, it can *optionally* take a path value, or no path at all.

In other situations, an argument can take a minimum amount of values (usually 1), but can receive arguments indefinitely (e.g. `cat file_0.txt file_1.txt file_2.txt`...). For such cases, the character `+` (regex inspired again) can be added after the number of expected arguments. This applies for both positional arguments and flags.

```
paths_in[]1+.PATH   # would be appropriate for the cat command example
~name[f,flag]1+.STR # same applies for flags
```

Finally, freyacli allows to have either 0 or as many values passed to an argument, by using the `*` character (regex inspired) after the square brackets. This time, no number is to be provided, as it wouldn't make sense.

```
paths_in[]*.PATH
~name[f,flag]*.STR
```
For real life usage of such positional arguments, imagine a text editor TUI application like `nano`: it can be launched without arguments (opens an empty editor) or it can be given multiple paths to open. Using it for flags is more rare, but there could be similar situations as the one described for `git`'s `--exec-path` flag and in which unlimited values are needed.


### Subcommands
Freya applications have a hierarchy of *subcommand* arguments that must be provided at the beginning of the CLI, before determining which are the appropriate positionals or flags to be considered. This is inspired by the CLI of complex applications such as `git` or `conda`, where the user can deal with different kind of commands depending on the operation they need.

Subcommands are to specified in a nested way inside both the `FYR` and `FYH` strings, by wrapping the inner nodes in between the `@some_name` and `!@` keywords. Here, `some_name` is the name of the respective subcommand (it's both the internal name **and** what the user needs to type in the CLI for accessing the subcommand). Subcommands can be nested multiple times, for example:
```
@install
    @local
        path[]1.PATH
    !@
    @fetch
        url[]1.STR
    !@
!@

@uninstall
    ~unattended[y,yes]
!@

@clean
    ~purge[p,purge]
!@
```

As seen in the example, this is useful for enforcing mutually exclusive arguments that take concrete values. For example, the user would need to type either `app install local` or `app install fetch` and can't combine both options. Freya itself will also prohibit something like `app install weird`, without the need for the developer to manually perform the assertion.


### Macros
Freya can perform macro substitution on both `FYR` and `FYH` strings when parsing. You can create a macro by wrapping any text around the `!def some_name` and `!fed` keywords, where `some_name` is the macro identifier. Later, by writing `!use:some_name` (no spaces), freyacli will preprocess the string with a simple text substitution. macros can appear before or after their usage, just don't declare macros inside other macro declarations.

#### Original FYR string
```
!def comon_arguments
    path_in[]1.PATH
    path_out[]1.PATH
    ~verbose[v,verbose]
!fed

@mode_0
    !use:common_arguments
    ~backup[b,backup]
    !use:one_liner
!@
@mode_1
    !use:common_arguments
    ~options[o,options]1+.STR
!@

### one-liners are also allowed, as long as spacing rules are respected
!def one_liner ~x[x,]1.FLOAT ~y[y,]1.FLOAT ~z[z,]1.FLOAT !fed

```

#### After macro substitution preprocessing
```
@mode_0
    path_in[]1.PATH
    path_out[]1.PATH
    ~verbose[v,verbose]
    ~backup[b,backup]
    ~x[x,]1.FLOAT
    ~y[y,]1.FLOAT
    ~z[z,]1.FLOAT
!@
@mode_1
    path_in[]1.PATH
    path_out[]1.PATH
    ~verbose[v,verbose]
    ~options[o,options]1+.STR
!@
```

### Help String
...


## Current limitations (TODO)
- Default values shouldn't have spaces or newlines inside
- Flag --help/-h is currently reserved.
- Positional arguments / options (flags) aren't currently supported for non-leaf **subcommand** nodes.
- Execution of the app must currently happen at a leaf **subcommand** node.
- Short flag names should not be a digit. Otherwise the parser will confuse it as a float value (e.g. `-3`).
