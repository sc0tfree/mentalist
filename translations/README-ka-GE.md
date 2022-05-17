![Version 1.0](http://img.shields.io/badge/version-v1.0-orange.svg)
![Python 3.6](http://img.shields.io/badge/python-3.6-blue.svg)
![MIT License](http://img.shields.io/badge/license-MIT%20License-blue.svg)
[![sc0tfree Twitter](http://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Follow)](https://twitter.com/sc0tfree)

# Mentalist
<p align="center">
  <img src="https://sc0tfree.squarespace.com/s/Mentalist-logo-250px.png" alt="Logo"/>
</p>
<br>

Mentalist არის გრაფიკული ინსტრუმენტი, რომელიც ინდივიდუალური (მორგებული) სიტყვათა სიების შესაქმნელად გამოიყენება. იგი პაროლის აგებისას ადამიანების მიერ ხშირად გამოყენებულ პარადიგმებს იყენებს და შეუძლია შედეგად დაგვიბრუნოს სრული სიტყვათა სია, ისევე როგორც [Hashcat](https://hashcat.net/hashcat)-თან და [John the Ripper](http://www.openwall.com/john)-თან თავსებადი წესები.
<br>

Mentalist-ის ინსტალაციისა და გამოყენების შესახებ დეტალური ინფორმაციის მისაღებად **[ეწვიეთ ვიკის](https://www.github.com/sc0tfree/mentalist/wiki)**.

<br>
<p align="center">
  <img src="https://sc0tfree.squarespace.com/s/mentalist-readme-gui.gif" alt="Mentalist GUI"/>
</p>

სწრაფად გასამართად და გასაშვებად ჩამოტვირთეთ წინასწარ გამზადებული, შესრულებადი (executable) ვარიანტი [ვერსიების გვერდიდან](https://github.com/sc0tfree/mentalist/releases).

## პასუხისმგებლობის უარყოფა

Mentalist გამოყენებულ უნდა იქნეს მხოლოდ **საინფორმაციო მიზნებისთვის** ან **სანქციონირებული სისტემების შემოწმებისთვის**. _არ გამოიყენოთ ეს ინსტრუმენტი სისტემაზე უკანონო წვდომის მოსაპოვებლად._

## ლიცენზია და წვლილის შეტანა

Mentalist ექვემდებარება MIT-ლიცენზიას.

წვლილის შეტანის მსურველებს ყოველთვის მივესალმებით! თუ გაქვთ სურვილი იხილოთ რაიმე კონკრეტული ფუნქცია Mentalist-ის შემდგომ ვერსიაში, გთხოვთ, მაცნობეთ.

## მადლობა

განსაკუთრებული მადლობა კრეიგ ბეიკერს, რომელმაც ხელი შეუწყო Mentalist-ის backend-ლოგიკის შექმნას. ასევე, მადლობა შეინ კარლიონს, რომლის Tkinter-fu აღმოჩნდა ფასდაუდებელი, და გრეგორი ბრიუერს, რომელმაც ამ პროექტის მხატვრული გაფორმება უზრუნველყო.

## შენიშვნა „ჟარგონებისა და სიტყვა-პარაზიტების“ სიასთან დაკავშირებით

სხვადასხვა წყაროებზე დაყრდნობით შედგენილი, ჩაშენებული `ჟარგონებისა და სიტყვა-პარაზიტების` სიის გამო განაწყენებულ ყოველ ადამიანს ბოდიშს ვუხდი. რეალურად, ზოგიერთი ადამიანი პაროლად იყენებს ჭეშმარიტად საზიზღარ სიტყვებს, ხოლო აღნიშნული სია მსგავსი პაროლების გასატეხად არის გათვალისწინებული (შედგენილი).

## სამერმისო სამუშაო

* ვებსაიტების ატრიბუტების სახით ფხეკის (scrape) შესაძლებლობა სიტყვათა ფუძეების კვანძში.
* სხვა ენებისათვის შესაბამისი ლექსიკონებისა და სიების დამატება.
* კვანძების (Nodes) დამატებისთვის/მომზადებისთვის გაერთიანებული სამეფოს საფოსტო კოდების დამატება.
* სიტყვათა ფუძეების გამეორებადობის გამორიცხვის შესაძლებლობა.
* Mentalist Chain ფაილის გამორჩევა.