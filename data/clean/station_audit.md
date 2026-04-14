# Station Audit Log

Audit of every station row in `matched_stations.csv` (the data that drives the reFuel UI). Each entry is checked for name/address consistency after two upstream fixes:

1. **Scraper filter** — `scripts/clean_google.py` drops Google Maps entries whose names indicate non-petrol businesses (mechanics, tyre shops, car washes, dealerships, workshops). Dropped on this run: 1 row (`Ryde Automative` @ 332 Blaxland Rd).
2. **Matcher street-number rule** — `scripts/merge_matched.py` now rejects matches where both addresses expose numeric street numbers that cannot overlap (e.g. 332 vs 326-328). This is what the original Ryde Automative bug exploited.

## Summary

| Bucket | Count |
|---|---|
| Correct | 320 |
| Incorrect | 0 |
| Ambiguous | 0 |
| **Total** | 320 |

## Incorrect

Name + address combination is wrong — typically the matcher paired the wrong Google record when a better candidate existed (same address, same street number) but was left as an unmatched gap. These surface to the user as Frankenstein rows: right address, wrong business name.

**Root cause of remaining incorrect matches:** `merge_matched.py` Pass 1 (exact address match) breaks ties by iteration order, not coordinate distance. When Google has duplicate records for one real station (common during brand rebrands), it may pick the stale/mis-located one. Worth fixing as a follow-up.

_None._

## Ambiguous

Needs manual eyes — either no recognisable fuel-brand keyword in either name, or match distance is unusual and no clear better candidate exists.

_None flagged._

## Correct

Heuristically safe: brand alignment between Google and FuelCheck, OR FuelCheck-only entry (NSW gov authoritative data), OR Google-only entry whose name contains a recognised fuel-brand keyword.

- **EG Ampol Marsfield** — Cnr Epping & Balaclava Road, Marsfield NSW 2122
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=0.0m_ (status: `matched`)

- **Ampol Foodary Carlingford** — 131 Pennant Hills Rd, Carlingford NSW 2118
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=0.0m_ (status: `matched`)

- **7-Eleven Carlingford** — 243 Pennant Hills Road, Carlingford NSW 2118
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **BP Carlingford** — 712 Pennant Hills Road, Carlingford NSW 2118
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Mobil 1 Carlingford Car Care** — 482 North Rocks Rd, Carlingford NSW 2118
  - _G=['mobil'] FC=['mobil']; dist=0.0m_ (status: `matched`)

- **North Ryde Petroleum** — 118 Coxs Rd, North Ryde NSW 2113
  - _G=['north ryde petroleum', 'petroleum'] FC=['north ryde petroleum', 'petroleum']; dist=0.0m_ (status: `matched`)

- **Metro Petroleum Willoughby** — 599 Willoughby Rd, Willoughby NSW 2068
  - Google: `Metro Petroleum Willoughby` | FuelCheck: `Metro Willoughby`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=0.0m_ (status: `matched`)

- **Ampol Foodary Crows Nest** — 111-121 Falcon Street, Crows Nest NSW 2065
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=0.0m_ (status: `matched`)

- **Speedway Roseville** — 20-22 Babbage Rd, Roseville NSW 2069
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Metro Petroleum Thornleigh** — 169-171 Pennant Hills Rd, Thornleigh NSW 2120
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=0.0m_ (status: `matched`)

- **Speedway Cammeray** — 330 Miller St, Cammeray NSW 2062
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **BP Silverwater South** — 51 Egerton St, Silverwater NSW 2128
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **7-Eleven Camperdown** — 198 Parramatta Rd, Camperdown NSW 2050
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **U-Go Mount Colah** — 603 Pacific Hwy, Mount Colah NSW 2079
  - _G=['u-go'] FC=['u-go']; dist=0.0m_ (status: `matched`)

- **7-Eleven Enmore** — 22 Stanmore Street, Enmore NSW 2042
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **Metro Rozelle** — 127 Victoria Rd, Rozelle NSW 2039
  - _G=['metro'] FC=['metro']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Guildford** — 295 Woodville Rd, Guildford NSW 2161
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **7-Eleven Guildford West** — 534 Guildford Road West (Corner Fowler Road), Guildford West NSW 2161
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **BP Camperdown** — Cnr Parramatta & Missenden Roads, Camperdown NSW 2050
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Merrylands** — 398 Merrylands Rd (Cnr Fowler Rd), Merrylands NSW 2160
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **BP Potts Hill T/S** — 155-157 Rockwood Road, Yagoona NSW 2199
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Pymble** — 21 Ryde Rd, Pymble NSW 2073
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Wahroonga** — 1601 Pacific Hwy & Coonanbarra Rd, Wahroonga NSW 2076
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express St Ives** — 179-181 Mona Vale Rd, St Ives NSW 2075
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Annandale** — 124-126 Johnston Street, Annandale NSW 2038
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **Speedway Westmead** — 67-69 Hawkesbury Rd, Westmead NSW 2145
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Speedway Regents Park** — 27-29 Amy Steet, Regents Park NSW 2143
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Budget Erskineville** — 25-33 Erskineville Road, Erskineville NSW 2043
  - _G=['budget'] FC=['budget']; dist=0.0m_ (status: `matched`)

- **BP Merrylands West** — 65 Kenyons Road, Merrylands West NSW 2160
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Metro Fuel Alexandria** — 36 Henderson Road, Alexandria NSW 2015
  - _G=['metro', 'fuel'] FC=['metro', 'fuel']; dist=0.0m_ (status: `matched`)

- **Tanwar Petroleum** — 281 New Canterbury Rd, Lewisham NSW 2049
  - _G=['tanwar', 'petroleum'] FC=['tanwar', 'petroleum']; dist=0.0m_ (status: `matched`)

- **Speedway Villawood** — 45 Fairfield St, Villawood NSW 2163
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Caltex Chester Hill** — 41 Boundary Road, Chester Hill NSW 2162
  - _G=['caltex'] FC=['caltex']; dist=0.0m_ (status: `matched`)

- **Metro St Ives Chase** — 164 Warrimoo Avenue, St Ives Chase NSW 2075
  - _G=['metro'] FC=['metro']; dist=0.0m_ (status: `matched`)

- **Independent Turramurra** — 105 Eastern Rd, Turramurra NSW 2074
  - _G=['independent turramurra'] FC=['independent turramurra']; dist=0.0m_ (status: `matched`)

- **Speedway Woodpark** — 32-36 Woodpark Rd, Woodpark NSW 2164
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Speedway Wenty** — 55-57 Station St, Wentworthville NSW 2145
  - _G=['speedway'] FC=['speedway']; dist=0.0m_ (status: `matched`)

- **Enhance Merrylands** — 506 Merrylands Rd, Merrylands West NSW 2160
  - _G=['enhance'] FC=['enhance']; dist=0.0m_ (status: `matched`)

- **BP West Pymble** — 45 Yanko Rd, West Pymble NSW 2073
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **BP Woodpark Road** — 186 Woodpark Rd, Smithfield NSW 2164
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Otr Greystanes** — 661 Merrylands Rd, Greystanes NSW 2145
  - _G=['otr'] FC=['otr']; dist=0.0m_ (status: `matched`)

- **Metro Petroleum Westleigh** — 128 Duffy Av, Westleigh NSW 2120
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=0.0m_ (status: `matched`)

- **Otr Baulkham Hills** — Shell Petrol Station 363 Windsor Rd, Baulkham Hills NSW 2153
  - _G=['otr'] FC=['otr']; dist=0.0m_ (status: `matched`)

- **Metro Sefton** — 101 Hector St, Sefton NSW 2162
  - _G=['metro'] FC=['metro']; dist=0.0m_ (status: `matched`)

- **Shell North Rocks** — 264 North Rocks Rd, North Rocks NSW 2151
  - _G=['shell'] FC=['shell']; dist=0.0m_ (status: `matched`)

- **Astron Yagoona West** — 100 Rookwood Rd, Yagoona NSW 2199
  - _G=['astron'] FC=['astron']; dist=0.0m_ (status: `matched`)

- **7-Eleven Paddington** — Cnr Oxford St & Greens Rd, Paddington NSW 2021
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **7-Eleven Mosman** — 162A Spit Road (Corner Mitchell Road), Mosman NSW 2088
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **7-Eleven Mosman** — 45 Spit Road, Mosman NSW 2088
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.0m_ (status: `matched`)

- **Shell Reddy Express Cremorne** — 227 Military Rd, Cremorne NSW 2090
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.0m_ (status: `matched`)

- **EG Ampol Redfern** — 475 Cleveland St, Redfern NSW 2016
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=0.0m_ (status: `matched`)

- **Coles Express Neutral Bay** — 200-204 Ben Boyd Rd (Cnr Ernest St), Neutral Bay NSW 2089
  - _G=['coles express'] FC=['coles express']; dist=0.0m_ (status: `matched`)

- **Metro Fuel Cremorne** — 51 Spofforth St, Cremorne NSW 2090
  - _G=['metro', 'fuel'] FC=['metro', 'fuel']; dist=0.0m_ (status: `matched`)

- **BP Redfern** — 411-417 Cleveland St, Redfern NSW 2016
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **BP Fox Hills** — 152 Toongabbie Rd, Girraween NSW 2145
  - _G=['bp'] FC=['bp']; dist=0.0m_ (status: `matched`)

- **Metro Petroleum Wakeley** — 72 Thorney Rd, Fairfield West NSW 2165
  - Google: `Metro Petroleum Wakeley` | FuelCheck: `Metro Wakeley`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=0.1m_ (status: `matched`)

- **Ampol Foodary Waitara** — 59-61 Pacific Highway, Waitara NSW 2077
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=0.2m_ (status: `matched`)

- **7-Eleven** — 575-585 Liverpool Road, Strathfield South NSW 2136
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Strathfield South`
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.7m_ (status: `matched`)

- **Speedway Court Rd Fairfield** — 32 Court Rd, Fairfield NSW 2165
  - Google: `Speedway Court Rd Fairfield` | FuelCheck: `Speedway Court Road`
  - _G=['speedway'] FC=['speedway']; dist=0.8m_ (status: `matched`)

- **Shell Reddy Express Lansvale** — 65-99 Hume Highway, Canley Vale NSW 2166
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=0.9m_ (status: `matched`)

- **U-Go Rozelle** — 121 Victoria Rd, Rozelle NSW 2039
  - Google: `U-Go Rozelle` | FuelCheck: `U-Go Rozelle (Self - Serve)`
  - _G=['u-go'] FC=['u-go']; dist=0.9m_ (status: `matched`)

- **BP** — Cnr Pacific Hwy & Bannockburn Rd, Pymble NSW 2073
  - Google: `BP` | FuelCheck: `BP Pymble`
  - _G=['bp'] FC=['bp']; dist=1.0m_ (status: `matched`)

- **BP Truckstop** — 149 Great Western Hwy, Mays Hill NSW 2145
  - Google: `BP Truckstop` | FuelCheck: `BP Mays Hill`
  - _G=['bp'] FC=['bp']; dist=1.8m_ (status: `matched`)

- **Budget Petrol Auburn** — 98 Park Rd, Auburn NSW 2144
  - Google: `Budget Petrol Auburn` | FuelCheck: `Budget Auburn`
  - _G=['budget'] FC=['budget']; dist=1.8m_ (status: `matched`)

- **EG Ampol** — 185 Pitt Street, Merrylands NSW 2160
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Merrylands`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=1.8m_ (status: `matched`)

- **Akshar Enterprise Pty Ltd T/A Power Fuel** — 101 Blaxcell St, Granville NSW 2142
  - Google: `Akshar Enterprise Pty Ltd T/A Power Fuel` | FuelCheck: `Powerfuel`
  - _G=['akshar', 'power fuel'] (FC bare); dist=1.8m_ (status: `matched`)

- **Enhance Bass Hill** — 924 Hume Hwy, Bass Hill NSW 2197
  - _G=['enhance'] FC=['enhance']; dist=1.9m_ (status: `matched`)

- **Barista Bar Metro Croydon Park** — 236-240 Georges River Rd, Croydon Park NSW 2133
  - Google: `Barista Bar Metro Croydon Park` | FuelCheck: `Metro Barista Bar Croydon Park`
  - _G=['metro'] FC=['metro']; dist=2.0m_ (status: `matched`)

- **Speedway South Granville (Clyde St)** — 171 Clyde St, South Granville NSW 2142
  - Google: `Speedway South Granville (Clyde St)` | FuelCheck: `Speedway South Granville`
  - _G=['speedway'] FC=['speedway']; dist=2.2m_ (status: `matched`)

- **Apw Store Wentworthville** — 449 Great Western Highway, Wentworthville NSW 2145
  - Google: `Apw Store Wentworthville` | FuelCheck: `Apw`
  - _G=['apw store'] (FC bare); dist=2.4m_ (status: `matched`)

- **U-Go Baulkham Hills** — 117 Seven Hills Rd, Baulkham Hills NSW 2153
  - Google: `U-Go Baulkham Hills` | FuelCheck: `U-Go Baulkham Hills (Unmanned)`
  - _G=['u-go'] FC=['u-go']; dist=2.6m_ (status: `matched`)

- **7-Eleven** — 342 Georges River Road & Burwood Road, Croydon Park NSW 2133
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Croydon Park`
  - _G=['7-eleven'] FC=['7-eleven']; dist=2.6m_ (status: `matched`)

- **BP** — 257 Guildford Rd, Guildford NSW 2161
  - Google: `BP` | FuelCheck: `BP Guildford`
  - _G=['bp'] FC=['bp']; dist=3.0m_ (status: `matched`)

- **BP Truckstop Fairfield** — 183 The Horsley Drive, Fairfield East NSW 2165
  - Google: `BP Truckstop Fairfield` | FuelCheck: `BP Fairfield`
  - _G=['bp'] FC=['bp']; dist=3.1m_ (status: `matched`)

- **7-Eleven** — 552 Pennant Hills Road, West Pennant Hills NSW 2125
  - Google: `7-Eleven` | FuelCheck: `7-Eleven West Pennant Hills`
  - _G=['7-eleven'] FC=['7-eleven']; dist=3.2m_ (status: `matched`)

- **Gas To Connect Guildford West** — 54C Fairfield Road, Guildford West NSW 2161
  - Google: `Gas To Connect Guildford West` | FuelCheck: `Gas To Connect`
  - _G=['gas to connect'] FC=['gas to connect']; dist=3.4m_ (status: `matched`)

- **Enhance Camellia** — 17 Grand Av, Camellia NSW 2142
  - _G=['enhance'] FC=['enhance']; dist=3.4m_ (status: `matched`)

- **Metro Petroleum Guildford** — 2 Rawson Road, Guildford NSW 2161
  - Google: `Metro Petroleum Guildford` | FuelCheck: `Metro Guildford`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=3.4m_ (status: `matched`)

- **Apex Petroleum** — 898-902 Victoria Rd, West Ryde NSW 2114
  - Google: `Apex Petroleum` | FuelCheck: `Apex Petroleum (West Ryde)`
  - Google addr: `898-902 Victoria Rd, West Ryde NSW`
  - FuelCheck addr: `898-902 Victoria Rd, West Ryde NSW 2114`
  - _G=['apex petroleum', 'petroleum'] FC=['apex petroleum', 'petroleum']; dist=3.7m_ (status: `matched`)

- **BP** — 580-586 Parramatta Road, Croydon NSW 2132
  - Google: `BP` | FuelCheck: `BP Ashfield`
  - _G=['bp'] FC=['bp']; dist=3.7m_ (status: `matched`)

- **Speedway William Street** — 2 Blaxcell St, Granville NSW 2142
  - _G=['speedway'] FC=['speedway']; dist=3.7m_ (status: `matched`)

- **Metro Petroleum Birrong** — 158 Auburn Rd, Birrong NSW 2143
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=3.8m_ (status: `matched`)

- **BP** — 184 Liverpool Road, Enfield NSW 2136
  - Google: `BP` | FuelCheck: `BP Enfield`
  - _G=['bp'] FC=['bp']; dist=3.9m_ (status: `matched`)

- **Shell Reddy Express Hunters Hill** — 4 Ryde Rd, Hunters Hill NSW 2110
  - Google addr: `4 Ryde Rd, Hunters Hill NSW`
  - FuelCheck addr: `4 Ryde Rd, Hunters Hill NSW 2110`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=4.0m_ (status: `matched`)

- **Budget Petrol North Strathfield** — 143 Concord Rd, North Strathfield NSW 2137
  - Google: `Budget Petrol North Strathfield` | FuelCheck: `Budget Petrol`
  - _G=['budget'] FC=['budget']; dist=4.1m_ (status: `matched`)

- **BP** — Pennant Hills Rd & Parkes St, Thornleigh NSW 2120
  - Google: `BP` | FuelCheck: `BP Thornleigh`
  - _G=['bp'] FC=['bp']; dist=4.1m_ (status: `matched`)

- **BP Dundas (Jasbe)** — 256 Kissing Point Rd, Dundas NSW 2117
  - Google: `BP Dundas (Jasbe)` | FuelCheck: `BP Dundas`
  - _G=['bp'] FC=['bp']; dist=4.2m_ (status: `matched`)

- **Apex Petroleum** — 896A Woodville Rd, Villawood NSW 2163
  - Google: `Apex Petroleum` | FuelCheck: `Apex Petroleum Villawood`
  - _G=['apex petroleum', 'petroleum'] FC=['apex petroleum', 'petroleum']; dist=4.2m_ (status: `matched`)

- **Ampol Foodary Rydalmere** — 309 Victoria Rd, Rydalmere NSW 2116
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=4.3m_ (status: `matched`)

- **Caltex Lane Cove** — 203 Burns Bay Rd, Lane Cove NSW 2066
  - Google: `Caltex Lane Cove` | FuelCheck: `Jack & Co Lane Cove`
  - _G=['caltex'] (FC bare); dist=4.4m_ (status: `matched`)

- **Metro Petroleum** — 172 Hector St, Chester Hill NSW 2162
  - Google: `Metro Petroleum` | FuelCheck: `Metro Petroleum Chester Hill`
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=4.4m_ (status: `matched`)

- **Ampol Foodary Homebush** — 334-336 Parramatta Rd, Homebush West NSW 2140
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=4.4m_ (status: `matched`)

- **Ampol Foodary Thornleigh** — 200-202 Pennant Hills Road, Thornleigh NSW 2120
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=4.4m_ (status: `matched`)

- **Shell** — 308-310 Parramatta Road, Stanmore NSW 2048
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Stanmore`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=4.6m_ (status: `matched`)

- **Coles Express Lansvale West** — 240 Hume Highway, Lansvale NSW 2166
  - _G=['coles express'] FC=['coles express']; dist=4.6m_ (status: `matched`)

- **Metro Petroleum Lane Cove** — 533 Mowbray Rd West, Lane Cove North NSW 2066
  - Google: `Metro Petroleum Lane Cove` | FuelCheck: `Metro Lane Cove North`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=4.7m_ (status: `matched`)

- **Ampol Foodary Concord** — 87-89 Parramatta Rd, Concord NSW 2137
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=4.7m_ (status: `matched`)

- **7-Eleven** — 477 Pacific Highway, Artarmon NSW 2064
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Artarmon`
  - _G=['7-eleven'] FC=['7-eleven']; dist=4.7m_ (status: `matched`)

- **Ampol Foodary Chatswood** — 572 Pacific Hwy, Chatswood NSW 2067
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=5.0m_ (status: `matched`)

- **Metro Petroleum Leichhardt** — 127-129 Marion St, Leichhardt NSW 2040
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=5.1m_ (status: `matched`)

- **Budget Petrol Chippendale** — 66-70 Regent Street, Chippendale NSW 2008
  - _G=['budget'] FC=['budget']; dist=5.2m_ (status: `matched`)

- **Speedway Bass Hill** — 972 Hume Highway, Bass Hill NSW 2197
  - _G=['speedway'] FC=['speedway']; dist=5.3m_ (status: `matched`)

- **BP** — 48-50 Aiken Road, West Pennant Hills NSW 2125
  - Google: `BP` | FuelCheck: `BP West Pennant Hills`
  - _G=['bp'] FC=['bp']; dist=5.6m_ (status: `matched`)

- **BP** — 316 Penshurst St, North Willoughby NSW 2068
  - Google: `BP` | FuelCheck: `BP Willoughby`
  - _G=['bp'] FC=['bp']; dist=5.7m_ (status: `matched`)

- **Metro Petroleum Greenacre** — 1 David St, Greenacre NSW 2190
  - Google: `Metro Petroleum Greenacre` | FuelCheck: `Metro Greenacre`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=5.7m_ (status: `matched`)

- **Shell** — 884-888 Hume Hwy (Cnr Strickland St), Bass Hill NSW 2197
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Bass Hill`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=5.7m_ (status: `matched`)

- **Metro Toongabbie** — 5 Picasso Cr, Old Toongabbie NSW 2146
  - _G=['metro'] FC=['metro']; dist=5.8m_ (status: `matched`)

- **7-Eleven** — 295-297 Merrylands Road (Corner Windsor Street), Merrylands NSW 2160
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Merrylands`
  - _G=['7-eleven'] FC=['7-eleven']; dist=5.8m_ (status: `matched`)

- **Metro Petroleum Epping** — 30 Bridge St, Epping NSW 2121
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=5.9m_ (status: `matched`)

- **Ampol Foodary St Ives** — 164 Mona Vale Road, St Ives NSW 2075
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=6.0m_ (status: `matched`)

- **BP Baulkham Hills** — 134 Seven Hills Rd, Baulkham Hills NSW 2153
  - _G=['bp'] FC=['bp']; dist=6.0m_ (status: `matched`)

- **BP** — 500 Willoughby Rd, Willoughby NSW 2068
  - Google: `BP` | FuelCheck: `BP Willoughby`
  - _G=['bp'] FC=['bp']; dist=6.0m_ (status: `matched`)

- **Metro Petroleum Haberfield** — 163-165 Parramatta Rd, Haberfield NSW 2045
  - Google: `Metro Petroleum Haberfield` | FuelCheck: `Metro Petroleum (Haberfield)`
  - _G=['metro', 'petroleum'] FC=['metro', 'petroleum']; dist=6.1m_ (status: `matched`)

- **7-Eleven Pendle Hill** — 217 Wentworth Avenue (Corner Bungaree Road), Pendle Hill NSW 2145
  - _G=['7-eleven'] FC=['7-eleven']; dist=6.1m_ (status: `matched`)

- **Budget Petrol - Lewisham** — 204-208 New Canterbury Rd, Lewisham NSW 2049
  - Google: `Budget Petrol - Lewisham` | FuelCheck: `Budget Petrol Lewisham`
  - _G=['budget'] FC=['budget']; dist=6.3m_ (status: `matched`)

- **7-Eleven** — 132 Liverpool Rd, Ashfield NSW 2131
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Ashfield`
  - _G=['7-eleven'] FC=['7-eleven']; dist=6.3m_ (status: `matched`)

- **BP** — 157 Penshurst Street, Willoughby NSW 2068
  - Google: `BP` | FuelCheck: `BP North Willoughby`
  - _G=['bp'] FC=['bp']; dist=6.4m_ (status: `matched`)

- **EG Ampol West Ryde** — 924 Victoria Rd, West Ryde NSW 2114
  - Google addr: `924 Victoria Rd, West Ryde NSW`
  - FuelCheck addr: `924 Victoria Rd, West Ryde NSW 2114`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=6.7m_ (status: `matched`)

- **Budget Petrol** — 365 Liverpool Rd, Strathfield NSW 2135
  - _G=['budget'] FC=['budget']; dist=6.7m_ (status: `matched`)

- **Shell** — 18 Parramatta Road, Lidcombe NSW 2141
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Lidcombe`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=6.9m_ (status: `matched`)

- **Ampol Foodary Pendle Hill** — 602-606 Great Western Hwy, Pendle Hill NSW 2145
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=6.9m_ (status: `matched`)

- **Speedway Auburn Road** — 74-78 Auburn Rd, Auburn NSW 2144
  - _G=['speedway'] FC=['speedway']; dist=7.0m_ (status: `matched`)

- **Speedway Granville (Blaxcell St)** — 348 Blaxcell Street, Granville NSW 2142
  - Google: `Speedway Granville (Blaxcell St)` | FuelCheck: `Speedway Granville`
  - _G=['speedway'] FC=['speedway']; dist=7.2m_ (status: `matched`)

- **Ampol Foodary Five Dock** — Ramsay Rd & Fairlight Street, Five Dock NSW 2046
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=7.2m_ (status: `matched`)

- **BP** — 295 Quarry Rd, Denistone East NSW 2112
  - Google: `BP` | FuelCheck: `BP Denistone East`
  - _G=['bp'] FC=['bp']; dist=7.5m_ (status: `matched`)

- **Prime Petrol Petersham** — 8 Crystal St, Petersham NSW 2049
  - Google: `Prime Petrol Petersham` | FuelCheck: `Prime Petersham`
  - _G=['prime petrol'] (FC bare); dist=7.6m_ (status: `matched`)

- **BP** — 422 Pacific Hwy, Artarmon NSW 2064
  - Google: `BP` | FuelCheck: `BP Artarmon`
  - _G=['bp'] FC=['bp']; dist=7.6m_ (status: `matched`)

- **EG Ampol** — 774 Parramatta Road, Lewisham NSW 2049
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Lewisham`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=7.6m_ (status: `matched`)

- **EG Ampol** — 35 Woodville Road (Cnr Alpha), Chester Hill NSW 2162
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Chester Hill`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=7.7m_ (status: `matched`)

- **Shell** — 38-46 Victoria Rd, Drummoyne NSW 2047
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Drummoyne`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=7.8m_ (status: `matched`)

- **BP** — 169 Willoughby Road, Naremburn NSW 2065
  - Google: `BP` | FuelCheck: `BP Naremburn`
  - _G=['bp'] FC=['bp']; dist=7.9m_ (status: `matched`)

- **EG Ampol Chatswood East** — 364-366 Eastern Valley Way, Chatswood East NSW 2067
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=8.0m_ (status: `matched`)

- **7-Eleven** — 1579 Pacific Highway (Corner Redleaf Avenue), Wahroonga NSW 2076
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Wahroonga`
  - _G=['7-eleven'] FC=['7-eleven']; dist=8.0m_ (status: `matched`)

- **Ampol Foodary Lane Cove West** — Unit 1 237-245 Burns Bay Rd, Lane Cove West NSW 2066
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=8.2m_ (status: `matched`)

- **Shell** — 378 Pacific Hwy (Cnr Allison Ave), Lane Cove NSW 2066
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Lane Cove`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=8.2m_ (status: `matched`)

- **7-Eleven** — 157-159 Mona Vale Rd, St Ives NSW 2075
  - Google: `7-Eleven` | FuelCheck: `7-Eleven St Ives`
  - _G=['7-eleven'] FC=['7-eleven']; dist=8.3m_ (status: `matched`)

- **Metro Petroleum Lansdowne** — 987 Hume Hwy, Lansdowne NSW 2163
  - Google: `Metro Petroleum Lansdowne` | FuelCheck: `Metro Lansdowne`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=8.3m_ (status: `matched`)

- **BP** — 1233 Victoria Road (Cnr Marsden Rd), West Ryde NSW 2114
  - Google: `BP` | FuelCheck: `BP West Ryde`
  - _G=['bp'] FC=['bp']; dist=8.5m_ (status: `matched`)

- **Shell Reddy Express Drummoyne South** — 39- 51 Victoria Rd, Drummoyne NSW 2047
  - Google: `Shell Reddy Express Drummoyne South` | FuelCheck: `Shell Reddy Express Drummoyne`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=8.5m_ (status: `matched`)

- **BP Concord (Wild Bean Cafe)** — 20 Burwood Road, Concord NSW 2137
  - Google: `BP Concord (Wild Bean Cafe)` | FuelCheck: `BP Concord`
  - _G=['bp'] FC=['bp']; dist=8.6m_ (status: `matched`)

- **EG Ampol** — 400 Parramatta Road, Burwood NSW 2134
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Burwood`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=9.0m_ (status: `matched`)

- **Shell** — 386 Pennant Hills Rd, Pennant Hills NSW 2120
  - Google: `Shell` | FuelCheck: `Otr Pennant Hills West`
  - _G=['shell'] FC=['otr']; dist=9.1m_ (status: `matched`)

- **Shell** — 188-190 Pennant Hills Rd, Thornleigh NSW 2120
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Thornleigh`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=9.2m_ (status: `matched`)

- **EG Ampol Turramurra** — 1233 Pacific Highway, Turramurra NSW 2074
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=9.3m_ (status: `matched`)

- **Metro Villawood Truckstop** — 276 Miller Rd, Villawood NSW 2163
  - Google: `Metro Villawood Truckstop` | FuelCheck: `Metro Villawood`
  - _G=['metro'] FC=['metro']; dist=9.6m_ (status: `matched`)

- **Speedway Auburn** — 238 Cumberland Rd, Auburn NSW 2144
  - _G=['speedway'] FC=['speedway']; dist=9.7m_ (status: `matched`)

- **Budget Petrol Telopea** — 57 Adderton Rd, Telopea NSW 2117
  - _G=['budget'] FC=['budget']; dist=10.0m_ (status: `matched`)

- **EG Ampol Fairfield Heights** — 163 The Boulevarde, Fairfield Heights NSW 2165
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=10.0m_ (status: `matched`)

- **7-Eleven** — 25 Parramatta Road, Haberfield NSW 2045
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Haberfield`
  - _G=['7-eleven'] FC=['7-eleven']; dist=10.3m_ (status: `matched`)

- **U-Go Carlingford Court** — 797 Pennant Hills Road, Carlingford NSW 2118
  - Google: `U-Go Carlingford Court` | FuelCheck: `U-Go Carlingford Court (Self- Serve)`
  - _G=['u-go'] FC=['u-go']; dist=10.5m_ (status: `matched`)

- **Metro Petroleum Canley Heights** — 190 Canley Vale Rd, Canley Heights NSW 2166
  - Google: `Metro Petroleum Canley Heights` | FuelCheck: `Metro Canley Heights`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=10.6m_ (status: `matched`)

- **BP** — 62-70 Epping Rd, Lane Cove NSW 2066
  - Google: `BP` | FuelCheck: `BP Lane Cove`
  - _G=['bp'] FC=['bp']; dist=10.7m_ (status: `matched`)

- **Ampol Foodary Strathfield South** — 600 Liverpool Rd, Strathfield South NSW 2136
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=10.8m_ (status: `matched`)

- **7-Eleven** — 45 Georges River Road, Croydon Park NSW 2133
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Croydon Park`
  - _G=['7-eleven'] FC=['7-eleven']; dist=10.9m_ (status: `matched`)

- **Metro Petroleum** — 275 Pacific Highway, Hornsby NSW 2077
  - Google: `Metro Petroleum` | FuelCheck: `Metro Fuel Hornsby`
  - _G=['metro', 'petroleum'] FC=['metro', 'fuel']; dist=11.3m_ (status: `matched`)

- **Ampol** — 179 Parramatta Road, Auburn NSW 2144
  - Google: `Ampol` | FuelCheck: `Ampol Auburn`
  - _G=['ampol'] FC=['ampol']; dist=11.4m_ (status: `matched`)

- **Shell** — 369 Pennant Hills Rd, Pennant Hills NSW 2120
  - Google: `Shell` | FuelCheck: `Otr Pennant Hills East`
  - _G=['shell'] FC=['otr']; dist=11.4m_ (status: `matched`)

- **Budget Petrol** — 37 Crystal St., Petersham NSW 2049
  - _G=['budget'] FC=['budget']; dist=11.4m_ (status: `matched`)

- **Shell** — 194-206 Pacific Hwy, Hornsby NSW 2077
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Hornsby`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=11.5m_ (status: `matched`)

- **BP** — 175 Ourimbah Road, Mosman NSW 2088
  - Google: `BP` | FuelCheck: `BP Mosman (9542)`
  - _G=['bp'] FC=['bp']; dist=11.6m_ (status: `matched`)

- **Shell Reddy Express West Ryde** — 1032-1036 Victoria Rd, West Ryde NSW 2114
  - Google: `Shell Reddy Express West Ryde` | FuelCheck: `Coles Express West Ryde`
  - Google addr: `1032-1036 Victoria Rd, West Ryde NSW`
  - FuelCheck addr: `1032-1036 Victoria Rd, West Ryde NSW 2114`
  - _G=['shell', 'reddy express'] FC=['coles express']; dist=11.7m_ (status: `matched`)

- **7-Eleven** — 272-278 Woodville Road, Guildford NSW 2161
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Guildford`
  - _G=['7-eleven'] FC=['7-eleven']; dist=11.7m_ (status: `matched`)

- **BP Truckstop** — Cnr Victora Rd & Clyde St, Rydalmere NSW 2116
  - Google: `BP Truckstop` | FuelCheck: `BP Rydalmere`
  - _G=['bp'] FC=['bp']; dist=11.9m_ (status: `matched`)

- **Shell** — 254 Burns Bay Rd, Lane Cove NSW 2066
  - Google: `Shell` | FuelCheck: `Shell Lane Cove`
  - _G=['shell'] FC=['shell']; dist=12.0m_ (status: `matched`)

- **7-Eleven** — 154-160 Parramatta Road & Corner Bold Street, Granville NSW 2142
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Granville`
  - _G=['7-eleven'] FC=['7-eleven']; dist=12.1m_ (status: `matched`)

- **Shell Ultimo** — 387 427 Wattle St, Ultimo NSW 2007
  - Google: `Shell Ultimo` | FuelCheck: `Coles Express Ultimo`
  - _G=['shell'] FC=['coles express']; dist=12.3m_ (status: `matched`)

- **Metro Petroleum Pendle Hill** — 229 Wentworth Avenue, Pendle Hill NSW 2145
  - Google: `Metro Petroleum Pendle Hill` | FuelCheck: `Metro Pendle Hill`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=12.5m_ (status: `matched`)

- **EG Ampol Strathfield** — 287 Liverpool Road, Burwood NSW 2134
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=12.6m_ (status: `matched`)

- **Shell** — 9 Albert Rd, Strathfield NSW 2135
  - Google: `Shell` | FuelCheck: `Otr Strathfield`
  - _G=['shell'] FC=['otr']; dist=12.6m_ (status: `matched`)

- **Shell** — 877-879 Pacific Hwy, Chatswood NSW 2067
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Chatswood`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=13.0m_ (status: `matched`)

- **7-Eleven** — 231-235 Great North Road, Five Dock NSW 2046
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Five Dock`
  - _G=['7-eleven'] FC=['7-eleven']; dist=13.2m_ (status: `matched`)

- **7-Eleven** — 1408 Pacific Highway (Corner Duff Street), Turramurra NSW 2074
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Turramurra`
  - _G=['7-eleven'] FC=['7-eleven']; dist=13.5m_ (status: `matched`)

- **BP** — 7 Northwood Rd, Longueville NSW 2066
  - Google: `BP` | FuelCheck: `Jack & Co Northwood`
  - _G=['bp'] (FC bare); dist=13.7m_ (status: `matched`)

- **Metro Petroleum Croydon Park** — 274 Georges River Rd, Croydon Park NSW 2133
  - Google: `Metro Petroleum Croydon Park` | FuelCheck: `Metro Fuel Croydon Park`
  - _G=['metro', 'petroleum'] FC=['metro', 'fuel']; dist=13.7m_ (status: `matched`)

- **BP** — Cnr Avenue & Cowles Roads, Mosman NSW 2088
  - Google: `BP` | FuelCheck: `BP Mosman (0926)`
  - _G=['bp'] FC=['bp']; dist=14.5m_ (status: `matched`)

- **Metro Petroleum Castle Cove** — 327 Eastern Valley Way, Castle Cove NSW 2069
  - Google: `Metro Petroleum Castle Cove` | FuelCheck: `Metro Castle Cove`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=14.6m_ (status: `matched`)

- **BP** — 95-97 Ramsay St, Haberfield NSW 2045
  - Google: `BP` | FuelCheck: `BP Haberfield`
  - _G=['bp'] FC=['bp']; dist=14.7m_ (status: `matched`)

- **BP** — 155 Pennant Hills Rd, Normanhurst NSW 2076
  - Google: `BP` | FuelCheck: `BP Normanhurst`
  - _G=['bp'] FC=['bp']; dist=14.9m_ (status: `matched`)

- **7-Eleven** — 238 Pacific Highway, Lindfield NSW 2070
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Lindfield`
  - _G=['7-eleven'] FC=['7-eleven']; dist=15.3m_ (status: `matched`)

- **EG Ampol** — 158 Clyde Street (Cnr Redfern St), Granville NSW 2142
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Granville`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=15.6m_ (status: `matched`)

- **7-Eleven** — 301 Hume Hwy, Greenacre NSW 2190
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Greenacre`
  - _G=['7-eleven'] FC=['7-eleven']; dist=15.7m_ (status: `matched`)

- **Metro Fuel Greystanes** — 73 Ettalong Rd, Greystanes NSW 2145
  - _G=['metro', 'fuel'] FC=['metro', 'fuel']; dist=16.0m_ (status: `matched`)

- **Ampol Foodary Granville** — 144 Parramatta Rd, Granville NSW 2142
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=16.3m_ (status: `matched`)

- **Shell Otr Willoughby** — 616-626 Willoughby Rd, Willoughby NSW 2068
  - Google: `Shell Otr Willoughby` | FuelCheck: `Otr Willoughby`
  - _G=['shell', 'otr'] FC=['otr']; dist=17.0m_ (status: `matched`)

- **Fast & Ezy** — 38A Gilba Rd, Girraween NSW 2145
  - Google: `Fast & Ezy` | FuelCheck: `Liberty Girraween`
  - _G=['fast & ezy'] FC=['liberty']; dist=17.2m_ (status: `matched`)

- **BP Truckstop** — 3 Carlton Cres, Summer Hill NSW 2130
  - Google: `BP Truckstop` | FuelCheck: `BP Summer Hill`
  - _G=['bp'] FC=['bp']; dist=17.5m_ (status: `matched`)

- **Speedway Haberfield** — 273 Parramatta Rd, Haberfield NSW 2045
  - _G=['speedway'] FC=['speedway']; dist=17.6m_ (status: `matched`)

- **Shell** — 9-11 Roberts Road, Greenacre NSW 2190
  - Google: `Shell` | FuelCheck: `Coles Express Greenacre`
  - _G=['shell'] FC=['coles express']; dist=18.3m_ (status: `matched`)

- **Speedway Fairfield** — 251 The Horsley Drive, Fairfield NSW 2165
  - _G=['speedway'] FC=['speedway']; dist=18.6m_ (status: `matched`)

- **Temco Petroleum** — 190 Waterloo Rd, Greenacre NSW 2190
  - _G=['temco', 'petroleum'] FC=['temco', 'petroleum']; dist=18.6m_ (status: `matched`)

- **Metro Petroleum Hurlstone Park** — 13 Canterbury Rd, Canterbury NSW 2193
  - Google: `Metro Petroleum Hurlstone Park` | FuelCheck: `Metro Hurlstone Park`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=19.5m_ (status: `matched`)

- **Westside Petroleum** — 210 Guildford Road, Guildford NSW 2161
  - Google: `Westside Petroleum` | FuelCheck: `Supreme Petroleum Guildford`
  - _G=['petroleum'] FC=['petroleum']; dist=20.9m_ (status: `matched`)

- **BP Truckstop** — Cnr Silverwater Road & Derby Street, Silverwater NSW 2128
  - Google: `BP Truckstop` | FuelCheck: `BP Silverwater`
  - _G=['bp'] FC=['bp']; dist=21.0m_ (status: `matched`)

- **Bravo Fuel Station** — 133-137 Targo, Girraween NSW 2145
  - Google: `Bravo Fuel Station` | FuelCheck: `Bravo Girraween`
  - _G=['bravo fuel', 'fuel station'] (FC bare); dist=21.1m_ (status: `matched`)

- **Enhance Eastwood / Mini Stop Express** — 2 Lovell Rd, Eastwood NSW 2122
  - Google: `Enhance Eastwood / Mini Stop Express` | FuelCheck: `Enhance Eastwood`
  - Google addr: `2 Lovell Rd, Eastwood NSW`
  - FuelCheck addr: `2 Lovell Rd, Eastwood NSW 2122`
  - _G=['enhance'] FC=['enhance']; dist=21.3m_ (status: `matched`)

- **Ampol Foodary Merrylands** — 150 Woodville Rd, Merrylands NSW 2160
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=21.4m_ (status: `matched`)

- **Ampol Foodary Neutral Bay** — 16-38 Military Rd, Neutral Bay NSW 2089
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=21.8m_ (status: `matched`)

- **Ampol Hornsby Heights Petrol Station** — 110 Galston Rd., Hornsby Heights NSW 2077
  - Google: `Ampol Hornsby Heights Petrol Station` | FuelCheck: `Ampol Hornsby Heights`
  - _G=['ampol', 'petrol station'] FC=['ampol']; dist=22.8m_ (status: `matched`)

- **7-Eleven** — 271A Victoria Road, Drummoyne NSW 2047
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Drummoyne`
  - _G=['7-eleven'] FC=['7-eleven']; dist=23.0m_ (status: `matched`)

- **Shell Otr Greenacre West** — 74 Roberts Rd, Greenacre NSW 2190
  - Google: `Shell Otr Greenacre West` | FuelCheck: `Otr Greenacre West`
  - _G=['shell', 'otr'] FC=['otr']; dist=23.2m_ (status: `matched`)

- **Shell Reddy Express Enfield** — 630-634 Liverpool Road, Strathfield South NSW 2136
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=24.1m_ (status: `matched`)

- **Shell Urbanista** — 418-424 Liverpool Rd, Croydon NSW 2132
  - Google: `Shell Urbanista` | FuelCheck: `Shell Croydon`
  - _G=['shell'] FC=['shell']; dist=24.2m_ (status: `matched`)

- **Bobbin Head Petrol Station** — 313 Bobbin Head Road, North Turramurra NSW 2074
  - _G=['petrol station'] FC=['petrol station']; dist=24.6m_ (status: `matched`)

- **Metro Petroleum Yagoona** — 585 Hume Hwy, Yagoona NSW 2199
  - Google: `Metro Petroleum Yagoona` | FuelCheck: `Metro Yagoona`
  - _G=['metro', 'petroleum'] FC=['metro']; dist=25.5m_ (status: `matched`)

- **7-Eleven** — 494 Pacific Hwy, Killara NSW 2071
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Killara`
  - _G=['7-eleven'] FC=['7-eleven']; dist=26.0m_ (status: `matched`)

- **Ampol Foodary Croydon** — 404-410 Liverpool Rd, Croydon NSW 2132
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=26.0m_ (status: `matched`)

- **Metro Petroleum Lidcombe** — 134 John Street, Lidcombe NSW 2141
  - Google: `Metro Petroleum Lidcombe` | FuelCheck: `Metro Fuel Homebush`
  - _G=['metro', 'petroleum'] FC=['metro', 'fuel']; dist=31.2m_ (status: `matched`)

- **Budget Petrol** — 22 Charlotte Street, Ashfield NSW 2131
  - Google: `Budget Petrol` | FuelCheck: `Budget Petrol Ashfield`
  - _G=['budget'] FC=['budget']; dist=31.5m_ (status: `matched`)

- **7-Eleven** — Corner Pacific Highway And Boundary Street, Roseville NSW 2069
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Roseville`
  - _G=['7-eleven'] FC=['7-eleven']; dist=31.9m_ (status: `matched`)

- **Shell** — 275 Lane Cove Rd, North Ryde NSW 2113
  - Google: `Shell` | FuelCheck: `Shell Reddy Express North Ryde`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=33.6m_ (status: `matched`)

- **BP** — 213 Kissing Point Rd, Turramurra NSW 2074
  - Google: `BP` | FuelCheck: `BP Turramurra`
  - _G=['bp'] FC=['bp']; dist=34.4m_ (status: `matched`)

- **7-Eleven** — 246 Beecroft & Carlingford Roads, Epping NSW 2121
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Epping`
  - _G=['7-eleven'] FC=['7-eleven']; dist=35.0m_ (status: `matched`)

- **BP** — Cnr George St And Burdett St, Hornsby NSW 2077
  - Google: `BP` | FuelCheck: `BP Hornsby`
  - _G=['bp'] FC=['bp']; dist=36.1m_ (status: `matched`)

- **Shell** — 213-253 Parramatta Rd & Walker St, Five Dock NSW 2046
  - Google: `Shell` | FuelCheck: `Coles Express Five Dock`
  - _G=['shell'] FC=['coles express']; dist=36.6m_ (status: `matched`)

- **Budget Petrol** — 27 Woodville Rd, Granville NSW 2142
  - Google: `Budget Petrol` | FuelCheck: `Budget Granville`
  - _G=['budget'] FC=['budget']; dist=37.6m_ (status: `matched`)

- **Shell** — 477-483 Miller St & Palmer St, Cammeray NSW 2062
  - Google: `Shell` | FuelCheck: `Shell Reddy Express Cammeray`
  - _G=['shell'] FC=['shell', 'reddy express']; dist=38.0m_ (status: `matched`)

- **7-Eleven** — Cnr Parramatta & Shaftsbury Rds, Burwood NSW 2134
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Burwood`
  - _G=['7-eleven'] FC=['7-eleven']; dist=41.3m_ (status: `matched`)

- **7-Eleven** — Lot 3-4 Parramatta Road & Harbord Street, Granville East NSW 2142
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Granville East`
  - _G=['7-eleven'] FC=['7-eleven']; dist=42.8m_ (status: `matched`)

- **BP Truckstop** — Cnr Pacific Highway & Jersey Street, Asquith NSW 2077
  - Google: `BP Truckstop` | FuelCheck: `BP Asquith`
  - _G=['bp'] FC=['bp']; dist=43.7m_ (status: `matched`)

- **7-Eleven** — 178-184 Victoria Road (Corner Moodie Street), Rozelle NSW 2039
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Rozelle`
  - _G=['7-eleven'] FC=['7-eleven']; dist=44.9m_ (status: `matched`)

- **EG Ampol** — 97 Hume Highway, Chullora NSW 2190
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Chullora`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=46.0m_ (status: `matched`)

- **Speedway Park Rd** — 360 Park Rd, Regents Park NSW 2143
  - Google: `Speedway Park Rd` | FuelCheck: `Speedway Park Road`
  - _G=['speedway'] FC=['speedway']; dist=47.4m_ (status: `matched`)

- **Ampol Foodary Old Guildford** — 636-644 Woodville Rd, Old Guildford NSW 2161
  - Google: `Ampol Foodary Old Guildford` | FuelCheck: `Ampol Foodary Guildford`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=50.2m_ (status: `matched`)

- **BP** — Cnr Victoria Rd & Evans St, Rozelle NSW 2039
  - Google: `BP` | FuelCheck: `BP Rozelle`
  - _G=['bp'] FC=['bp']; dist=50.5m_ (status: `matched`)

- **BP** — Cnr Hassall & James Ruse Drive, Rosehill NSW 2142
  - Google: `BP` | FuelCheck: `BP Rosehill`
  - _G=['bp'] FC=['bp']; dist=56.1m_ (status: `matched`)

- **Ampol Foodary St Ives North** — 363 Mona Vale Road, St Ives North NSW 2075
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=57.8m_ (status: `matched`)

- **Shell** — 1 Durham St, Rosehill NSW 2142
  - Google: `Shell` | FuelCheck: `Shell Parramatta Cvro (Self-Serve)`
  - _G=['shell'] FC=['shell']; dist=58.5m_ (status: `matched`)

- **7-Eleven Lansvale** — 44 Hume Highway & Knight Street, Lansvale South NSW 2166
  - Google: `7-Eleven Lansvale` | FuelCheck: `7-Eleven Lansvale South`
  - _G=['7-eleven'] FC=['7-eleven']; dist=59.5m_ (status: `matched`)

- **EG Ampol Greenacre** — 51 Roberts Road (Cnr Amarina St), Greenacre NSW 2190
  - Google addr: `51 Roberts Rd (Cnr Amarina St), Greenacre NSW 2190`
  - FuelCheck addr: `51 Roberts Road (Cnr Amarina St), Greenacre NSW 2190`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=16.9m_ (status: `matched`)

- **Speedway Smithfield** — 26-28 Smithfield Road, Smithfield NSW 2164
  - Google addr: `26-28 Smithfield Rd, Smithfield NSW 2164`
  - FuelCheck addr: `26-28 Smithfield Road, Smithfield NSW 2164`
  - _G=['speedway'] FC=['speedway']; dist=0.1m_ (status: `matched`)

- **7-Eleven Fairfield** — 234 Hamilton Road, Fairfield West NSW 2165
  - Google: `7-Eleven Fairfield` | FuelCheck: `7-Eleven Fairfield West`
  - Google addr: `234 Hamilton Rd, Fairfield West NSW 2165`
  - FuelCheck addr: `234 Hamilton Road, Fairfield West NSW 2165`
  - _G=['7-eleven'] FC=['7-eleven']; dist=5.1m_ (status: `matched`)

- **Ampol Foodary Ermington** — 560-562 Victoria Road, Ermington NSW 2115
  - Google addr: `560-562 Victoria Rd, Ermington NSW`
  - FuelCheck addr: `560-562 Victoria Road, Ermington NSW 2115`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=7.0m_ (status: `matched`)

- **Calvi Petrol Station** — 320 Lane Cove Road, North Ryde NSW 2113
  - Google addr: `320 Lane Cove Rd, North Ryde NSW`
  - FuelCheck addr: `320 Lane Cove Road, North Ryde NSW 2113`
  - _G=['petrol station'] FC=['petrol station']; dist=10.7m_ (status: `matched`)

- **7-Eleven** — 400 Lane Cove Road, North Ryde NSW 2113
  - Google: `7-Eleven` | FuelCheck: `7-Eleven North Ryde`
  - Google addr: `400 Lane Cove Rd, North Ryde NSW`
  - FuelCheck addr: `400 Lane Cove Road, North Ryde NSW 2113`
  - _G=['7-eleven'] FC=['7-eleven']; dist=31.4m_ (status: `matched`)

- **Speedway West Ryde** — 899 Victoria Road, West Ryde NSW 2114
  - Google addr: `899 Victoria Rd, West Ryde NSW`
  - FuelCheck addr: `899 Victoria Road, West Ryde NSW 2114`
  - _G=['speedway'] FC=['speedway']; dist=28.7m_ (status: `matched`)

- **Shell Reddy Express Northmead** — 197 Windsor Road, Northmead NSW 2152
  - Google addr: `197 Windsor Rd, Northmead NSW`
  - FuelCheck addr: `197 Windsor Road, Northmead NSW 2152`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=7.9m_ (status: `matched`)

- **7-Eleven Northmead** — 137 Windsor Road, Northmead NSW 2152
  - Google addr: `137 Windsor Rd, Northmead NSW`
  - FuelCheck addr: `137 Windsor Road, Northmead NSW 2152`
  - _G=['7-eleven'] FC=['7-eleven']; dist=11.4m_ (status: `matched`)

- **Shell Reddy Express Northmead Briens** — 100 Briens Road, Northmead NSW 2152
  - Google addr: `100 Briens Rd, Northmead NSW`
  - FuelCheck addr: `100 Briens Road, Northmead NSW 2152`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=57.6m_ (status: `matched`)

- **Shell Reddy Express North Ryde Wicks** — 96 Wicks Road, North Ryde NSW 2113
  - Google addr: `96 Wicks Rd, North Ryde NSW`
  - FuelCheck addr: `96 Wicks Road, North Ryde NSW 2113`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=16.0m_ (status: `matched`)

- **Metro Petroleum** — 36-38 Lane Cove Rd, Ryde NSW 2112
  - Google: `Metro Petroleum` | FuelCheck: `Metro Fuel`
  - Google addr: `36 Lane Cove Rd, Ryde NSW`
  - FuelCheck addr: `36-38 Lane Cove Rd, Ryde NSW 2112`
  - _G=['metro', 'petroleum'] FC=['metro', 'fuel']; dist=17.8m_ (status: `matched`)

- **Shell Reddy Express Ryde** — 45 Lane Cove Rd & Myra Ave, Ryde NSW 2112
  - Google addr: `45 Lane Cove Rd, Ryde NSW`
  - FuelCheck addr: `45 Lane Cove Rd & Myra Ave, Ryde NSW 2112`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=9.2m_ (status: `matched`)

- **Speedway Kent Road** — 38 Kent Rd, North Ryde NSW 2113
  - Google addr: `34-38 Kent Rd, North Ryde NSW`
  - FuelCheck addr: `38 Kent Rd, North Ryde NSW 2113`
  - _G=['speedway'] FC=['speedway']; dist=2.3m_ (status: `matched`)

- **Ampol Foodary North Ryde** — 41-43 Epping Rd Cnr Wicks Rd, North Ryde NSW 2113
  - Google addr: `41-43 Epping Rd, North Ryde NSW`
  - FuelCheck addr: `41-43 Epping Rd Cnr Wicks Rd, North Ryde NSW 2113`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=7.3m_ (status: `matched`)

- **Shell Reddy Express Marsfield** — 189 Epping Rd & Culloden Rd, Marsfield NSW 2122
  - Google addr: `189 Epping Rd, Marsfield NSW`
  - FuelCheck addr: `189 Epping Rd & Culloden Rd, Marsfield NSW 2122`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=3.1m_ (status: `matched`)

- **EG Ampol** — 154 Silverwater Rd, Silverwater NSW 2128
  - Google: `EG Ampol` | FuelCheck: `EG Ampol Silverwater`
  - Google addr: `154 Silverwater Rd`
  - FuelCheck addr: `154 Silverwater Rd, Silverwater NSW 2128`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=22.9m_ (status: `matched`)

- **Shell Reddy Express Dundas** — 199-203 Kissing Point Rd (Cnr Kirby St), Dundas NSW 2117
  - Google addr: `199-203 Kissing Point Rd (Corner, Kirby St`
  - FuelCheck addr: `199-203 Kissing Point Rd (Cnr Kirby St), Dundas NSW 2117`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=62.0m_ (status: `matched`)

- **Speedway Parramatta** — 127A Alfred St, Parramatta NSW 2150
  - Google addr: `127A Alfred St`
  - FuelCheck addr: `127A Alfred St, Parramatta NSW 2150`
  - _G=['speedway'] FC=['speedway']; dist=6.2m_ (status: `matched`)

- **Shell Reddy Express Parramatta** — 88 Victoria Rd (Cnr Buller St), Parramatta NSW 2150
  - Google addr: `88 Victoria Rd (Corner, Buller St`
  - FuelCheck addr: `88 Victoria Rd (Cnr Buller St), Parramatta NSW 2150`
  - _G=['shell', 'reddy express'] FC=['shell', 'reddy express']; dist=64.3m_ (status: `matched`)

- **7-Eleven Northmead** — 56 Windsor Road & Northmead Avenue, Northmead NSW 2152
  - Google addr: `56 Windsor Rd, Northmead NSW`
  - FuelCheck addr: `56 Windsor Road & Northmead Avenue, Northmead NSW 2152`
  - _G=['7-eleven'] FC=['7-eleven']; dist=34.9m_ (status: `matched`)

- **Ampol Foodary Northmead** — 98-100 Windsor Rd Cnr Lombard Rd, Northmead NSW 2152
  - Google addr: `Windsor Rd Cnr, 98-100 Lombard St, Northmead NSW`
  - FuelCheck addr: `98-100 Windsor Rd Cnr Lombard Rd, Northmead NSW 2152`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=44.4m_ (status: `matched`)

- **Costco Fuel Lidcombe** — Costco 17-21 Parramatta Rd, Lidcombe NSW 2141
  - Google: `Costco Fuel Lidcombe` | FuelCheck: `Costco Auburn (Members Only)`
  - Google addr: `17-21 Parramatta Rd, Lidcombe NSW 2141`
  - FuelCheck addr: `Costco 17-21 Parramatta Rd, Lidcombe NSW 2141`
  - _G=['costco fuel', 'fuel'] (FC bare); dist=158.4m_ (status: `matched`)

- **Ampol Foodary Greenacre** — 87-91 Roberts Rd, Greenacre NSW 2190
  - Google addr: `87-91 Roberts Rd (Cnr Moondo St), Greenacre NSW 2190`
  - FuelCheck addr: `87-91 Roberts Rd, Greenacre NSW 2190`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=28.0m_ (status: `matched`)

- **EG Ampol Bass Hill** — 862 Hume Highway, Bass Hill NSW 2197
  - Google addr: `862 Hume Hwy, Bass Hill NSW 2197`
  - FuelCheck addr: `862 Hume Highway, Bass Hill NSW 2197`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=8.5m_ (status: `matched`)

- **Shell Urbanista** — 740 Hume Highway, Yagoona NSW 2199
  - Google: `Shell Urbanista` | FuelCheck: `Shell Yagoona`
  - Google addr: `740 Hume Hwy, Yagoona NSW 2199`
  - FuelCheck addr: `740 Hume Highway, Yagoona NSW 2199`
  - _G=['shell'] FC=['shell']; dist=6.5m_ (status: `matched`)

- **Budget Fairfield** — 62 Railway Parade, Fairfield NSW 2165
  - Google addr: `62 Railway Pde, Fairfield NSW 2165`
  - FuelCheck addr: `62 Railway Parade, Fairfield NSW 2165`
  - _G=['budget'] FC=['budget']; dist=16.0m_ (status: `matched`)

- **Ampol Foodary Lansvale** — 141-151 Hume Highway Cnr Chadderton St, Lansvale NSW 2166
  - Google addr: `141-151 Hume Highway, Lansvale NSW 2166`
  - FuelCheck addr: `141-151 Hume Highway Cnr Chadderton St, Lansvale NSW 2166`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=3.2m_ (status: `matched`)

- **EG Ampol Lansvale** — 136 Hume Highway (Cnr Hollywood Drive), Lansvale NSW 2166
  - Google addr: `136 Hume Highway, Lansvale NSW 2166`
  - FuelCheck addr: `136 Hume Highway (Cnr Hollywood Drive), Lansvale NSW 2166`
  - _G=['ampol', 'eg ampol'] FC=['ampol', 'eg ampol']; dist=1.5m_ (status: `matched`)

- **7-Eleven Greystanes** — 601-605 Great Western Highway, Greystanes NSW 2145
  - Google addr: `601-605 Great Western Hwy, Greystanes NSW 2145`
  - FuelCheck addr: `601-605 Great Western Highway, Greystanes NSW 2145`
  - _G=['7-eleven'] FC=['7-eleven']; dist=3.2m_ (status: `matched`)

- **Speedway Fairfield West** — 115 Sackville Street, Fairfield NSW 2165
  - Google: `Speedway Fairfield West` | FuelCheck: `Speedway Sackville Street Fairfield`
  - Google addr: `115 Sackville St, Fairfield NSW 2165`
  - FuelCheck addr: `115 Sackville Street, Fairfield NSW 2165`
  - _G=['speedway'] FC=['speedway']; dist=1.9m_ (status: `matched`)

- **BP Greystanes** — 2-4 Kippax St, Greystanes NSW 2145
  - Google addr: `Cnr Merrylands Rd & Kippax St, Greystanes NSW 2145`
  - FuelCheck addr: `2-4 Kippax St, Greystanes NSW 2145`
  - _G=['bp'] FC=['bp']; dist=2.9m_ (status: `matched`)

- **BP Putney** — 238 Morrison Rd, Putney NSW
  - _Google-only, brand=['bp']_ (status: `gap_google_only`)

- **Petro 711** — 919 Victoria Road (Corner Hermitage Road), West Ryde NSW 2114
  - Google: `Petro 711` | FuelCheck: `7-Eleven West Ryde`
  - Google addr: `917-921 Victoria Rd, West Ryde NSW`
  - FuelCheck addr: `919 Victoria Road (Corner Hermitage Road), West Ryde NSW 2114`
  - _G=['petro 711'] FC=['7-eleven']; dist=10.8m_ (status: `matched`)

- **Metro** — 700 Victoria Rd, Ermington NSW 2115
  - _Google-only, brand=['metro']_ (status: `gap_google_only`)

- **Medco Carlingford** — 286-288 Pennant Hills Road, Cnr Adderton Road, Carlingford NSW 2118
  - _Google-only, brand=['medco']_ (status: `gap_google_only`)

- **Astron Rydalmere** — 262 - 272 Victoria Rd Rydalmere NSW 2116
  - _Google-only, brand=['astron']_ (status: `gap_google_only`)

- **EG Ampol Newington** — 1 Ave Of The Americas
  - _Google-only, brand=['ampol', 'eg ampol']_ (status: `gap_google_only`)

- **Enhance Homebush** — 242 Parramatta Rd
  - _Google-only, brand=['enhance']_ (status: `gap_google_only`)

- **Ampol Foodary Lane Cove** — 237-245 Burns Bay Rd, Lane Cove West NSW 2066
  - _Google-only, brand=['ampol', 'foodary']_ (status: `gap_google_only`)

- **BP Truckstop** — 369 North Rocks Rd, North Rocks NSW 2151
  - Google: `BP Truckstop` | FuelCheck: `BP North Rocks`
  - Google addr: `369 N Rocks Rd`
  - FuelCheck addr: `369 North Rocks Rd, North Rocks NSW 2151`
  - _G=['bp'] FC=['bp']; dist=17.3m_ (status: `matched`)

- **7-Eleven** — 81 Victoria Road & Macarthur Street, Parramatta NSW 2150
  - Google: `7-Eleven` | FuelCheck: `7-Eleven Parramatta`
  - Google addr: `81 Macarthur St`
  - FuelCheck addr: `81 Victoria Road & Macarthur Street, Parramatta NSW 2150`
  - _G=['7-eleven'] FC=['7-eleven']; dist=52.3m_ (status: `matched`)

- **Ampol Foodary Parramatta** — 159 Wigram St, Parramatta NSW 2150
  - _Google-only, brand=['ampol', 'foodary']_ (status: `gap_google_only`)

- **Shell Reddy Express Parramatta North** — 88 Victoria Rd (Cnr Buller St), Parramatta NSW 2150
  - _Google-only, brand=['shell', 'reddy express']_ (status: `gap_google_only`)

- **7-Eleven** — 340 North Rocks Road, North Rocks NSW 2151
  - Google: `7-Eleven` | FuelCheck: `7-Eleven North Rocks`
  - Google addr: `340 N Rocks Rd`
  - FuelCheck addr: `340 North Rocks Road, North Rocks NSW 2151`
  - _G=['7-eleven'] FC=['7-eleven']; dist=0.1m_ (status: `matched`)

- **Enhance Eastwood** — 2 Lovell Rd, Eastwood NSW 2122
  - _Google-only, brand=['enhance']_ (status: `gap_google_only`)

- **7-Eleven** — 246 Beecroft Rd & Carlingford Rd, Epping NSW 2121
  - _Google-only, brand=['7-eleven']_ (status: `gap_google_only`)

- **United** — 117 Seven Hills Rd, Baulkham Hills NSW 2153
  - _Google-only, brand=['united']_ (status: `gap_google_only`)

- **Shell** — 1 Durham St, Rosehill NSW 2142
  - _Google-only, brand=['shell']_ (status: `gap_google_only`)

- **7-Eleven** — 575-585 Liverpool Rd, Strathfield South NSW 2136
  - _Google-only, brand=['7-eleven']_ (status: `gap_google_only`)

- **Shell Reddy Express Roberts Road East** — 74 Roberts Rd, Greenacre NSW 2190
  - _Google-only, brand=['shell', 'reddy express']_ (status: `gap_google_only`)

- **BP Truckstop** — 155-157 Rockwood Rd, Yagoona NSW 2199
  - _Google-only, brand=['bp']_ (status: `gap_google_only`)

- **7-Eleven** — 132 Hume Hwy & Victoria St, Ashfield NSW 2131
  - _Google-only, brand=['7-eleven']_ (status: `gap_google_only`)

- **Metro Petroleum Fairfield** — 113 Sackville St, Fairfield NSW 2165
  - _Google-only, brand=['metro', 'petroleum']_ (status: `gap_google_only`)

- **Metro Petroleum Fairfield 82** — 82-86 Hamilton Rd, Fairfield NSW 2165
  - _Google-only, brand=['metro', 'petroleum']_ (status: `gap_google_only`)

- **7-Eleven Baulkham Hills** — 224 Windsor Rd, Baulkham Hills NSW 2153
  - _Google-only, brand=['7-eleven']_ (status: `gap_google_only`)

- **BP Seven Hills** — Abbott Road, Seven Hills NSW 2147
  - Google addr: `Prospect Hwy & Redgum Ave, Seven Hills NSW 2147`
  - FuelCheck addr: `Abbott Road, Seven Hills NSW 2147`
  - _G=['bp'] FC=['bp']; dist=4.2m_ (status: `matched`)

- **BP Edgecliff** — 203 New South Head Rd, Edgecliff NSW 2027
  - _Google-only, brand=['bp']_ (status: `gap_google_only`)

- **Otr Woolloomooloo** — 1 Bourke St, Woolloomooloo NSW 2011
  - _Google-only, brand=['otr']_ (status: `gap_google_only`)

- **BP Woollahra** — 187 Oxford St, Woollahra NSW 2025
  - _Google-only, brand=['bp']_ (status: `gap_google_only`)

- **Shell Reddy Express Bondi Junction** — 194 Oxford St, Bondi Junction NSW 2022
  - _Google-only, brand=['shell', 'reddy express']_ (status: `gap_google_only`)

- **Ampol Foodary Seven Hills** — 38 Abbott Rd, Seven Hills NSW 2147
  - Google addr: `Prospect Hwy, Seven Hills NSW 2147`
  - FuelCheck addr: `38 Abbott Rd, Seven Hills NSW 2147`
  - _G=['ampol', 'foodary'] FC=['ampol', 'foodary']; dist=0.0m_ (status: `matched`)

- **Coles Express Yagoona** — 112 Rookwood (Cnr Brunker) Rds, Yagoona NSW 2199
  - Google addr: `Hume Hwy, Yagoona NSW 2199`
  - FuelCheck addr: `112 Rookwood (Cnr Brunker) Rds, Yagoona NSW 2199`
  - _G=['coles express'] FC=['coles express']; dist=0.0m_ (status: `matched`)

- **Westside Petroleum Lidcombe** — 32 Joseph St, Lidcombe NSW 2141
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Ampol Foodary Alexandria** — 133 Wyndham Street, Alexandria NSW 2015
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **7-Eleven Baulkham Hills** — 217-219 Seven Hills Rd, Baulkham Hills NSW 2153
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **7-Eleven Seven Hills** — 151 Prospect Hwy, Seven Hills NSW 2147
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **7-Eleven Yagoona** — 519 Hume Hwy, Yagoona NSW 2199
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Budget Petroleum Smithfield** — 729 The Horsley Dr, Smithfield NSW 2164
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Ampol Foodary Woollahra** — 116-118 Old South Head Rd, Woollahra NSW 2025
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **U-Go Canley Heights (Un-Manned)** — 280-282 Canley Vale Road, Canley Heights NSW 2166
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Smithfield NSW** — 846 The Horsley Drive, Smithfield NSW 2164
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Shell Reddy Express Smithfield** — 678 The Horsley Drv (Cnr Cumberland Hwy), Smithfield NSW 2164
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **7-Eleven Fairfield** — 320 Polding St, Fairfield West NSW 2165
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Shell Reddy Express Norwest Business Park** — 4 Century Circuit, Baulkham Hills NSW 2153
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Shell Reddy Express Alexandria** — 562-572 Botany Rd, Alexandria NSW 2015
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **7-Eleven Ryde** — 326-328 Blaxland Road, Ryde NSW 2112
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Canterbury** — 322 Canterbury Road, Canterbury NSW 2193
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Woollahra** — 39 Vernon Street, Woollahra NSW 2025
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Shell Reddy Express Bondi Junction** — 120-138 Birrell Street, Bondi Junction NSW 2022
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **EG Ampol Seven Hills North** — 1/155 Prospect Highway, Seven Hills NSW 2147
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **EG Ampol Seven Hills** — 240 Prospect Highway, Seven Hills NSW 2147
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Ampol Foodary Seven Hills** — 105 Station Rd Cnr Powers St, Seven Hills NSW 2147
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Metro Fuel Canterbury** — 280 Canterbury Road, Canterbury NSW 2193
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Speedway Horsley Drive** — 769 The Horsley Dr, Smithfield NSW 2164
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Metro Fuel Fairfield** — 130 Hamilton Road, Fairfield NSW 2165
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Yagoona** — 405 Hume Highway, Yagoona NSW 2199
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Edgecliff** — 67 New South Head Rd, Edgecliff NSW 2027
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Putney** — 236 Morrison Road, Putney NSW 2112
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **BP Seven Hills** — 154-156 Prospect Hwy, Seven Hills NSW 2147
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Astron Yagoona** — 45 Rookwood Rd, Yagoona NSW 2199
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

- **Otr Woolloomooloo** — 61 Cowper Wharf Roadway, Woolloomooloo NSW 2011
  - _FuelCheck gov data (authoritative)_ (status: `fuelcheck_only`)

