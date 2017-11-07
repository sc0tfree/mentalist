![Version 1.0](http://img.shields.io/badge/version-v1.0-orange.svg)
![Python 3.6](http://img.shields.io/badge/python-3.6-blue.svg)
![MIT License](http://img.shields.io/badge/license-MIT%20License-blue.svg)
[![sc0tfree Twitter](http://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Follow)](https://twitter.com/sc0tfree)

# Mentalist
<p align="center">
  <img src="https://sc0tfree.squarespace.com/s/Mentalist-logo-250px.png" alt="Logo"/>
</p>
<br>

Mentalist is a graphical tool for custom wordlist generation. It utilizes common human paradigms for constructing passwords and can output the full wordlist as well as rules compatible with [Hashcat](https://hashcat.net/hashcat) and [John the Ripper](http://www.openwall.com/john).
<br>

For more information on installing and using Mentalist, please **[visit the wiki](https://www.github.com/sc0tfree/mentalist/wiki)**.

<br>
<p align="center">
  <img src="https://sc0tfree.squarespace.com/s/mentalist-readme-gui.gif" alt="Mentalist GUI"/>
</p>

To get up and running quickly, download a prebuilt executable on the [releases page](https://github.com/sc0tfree/mentalist/releases).

## Disclaimer

Mentalist should be used only for **informational purposes** or on **authorized system audits**. _Do not use this tool to aid in illicit access to a system._

## License and Contributions

Mentalist is under the MIT License.

Contributions are always welcomed! Please let me know if there's a specific piece of functionality that you'd like to see built-in to the next version of Mentalist.

## Thanks

A special thanks to Craig Baker, who was instrumental in helping to develop the backend logic of Mentalist. Additionally, thank you to Shane Carlyon, whose Tkinter-fu was invaluable, and to Gregory Brewer, who contributed the artwork to this project.

## Note on ‘Slang and Expletives’ List

I apologize to anyone offended by the built-in list of `Slang & Expletives`, compiled from a variety of sources. The reality is that some people use truly heinous words for their credentials and this list is meant to help crack them.

## Future Work

* Ability to scrape sites as an attribute in the Base Words node.
* Add dictionaries and lists for more languages
* Add UK post codes to Append/Prepend Nodes
* Option to perform de-duplication of Base Words
* Mentalist Chain file differencing