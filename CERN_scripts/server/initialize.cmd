# Read DLL settings
#R8100
#R81DF
#R8200
#R82DF
# Add 100 ohm termination and remove pull-ups and downs
W4C040EAA
# Disable PLL CENTER bypass
W80620000
# Sets source of CLK_REF_PLL in 3 peripheries
WA02003901FC1
WC30003901FC1
W430003901FC1
#Enable PLL in 3 peripheries
WA02003905FC1
WC30003905FC1
W430003905FC1
# Start-up PLLs
WA02003905FE1
WC30003905FE1
W430003905FE1
# Start-up PLLs complete
WA02003905FC1
WC30003905FC1
W430003905FC1
# 8000 default 0800
W80000C00
# pixel matrix DLL power up
W80030200
W80030000
# enable clock propagation in whole pixel matri
W8070ffff
W8071ffff
W8072ffff
W8073ffff
W8074ffff
W8075ffff
W8076ffff
W8077ffff
W8078ffff
W8079ffff
W807affff
W807bffff
W807cffff
W807dffff
W8080ffff
W8081ffff
W8082ffff
W8083ffff
W8084ffff
W8085ffff
W8086ffff
W8087ffff
W8088ffff
W8089ffff
W808affff
W808bffff
W808cffff
W808dffff
# configure matrix reset sequencer, 5 banks
W80600028
# reset sequencially pixel matrix
#W80510006
#R8100
#R8101
#R81DF
#R8200
#R8201
#R82DF
