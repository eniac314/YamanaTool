module Yamana where

import Html exposing (..)
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import StartApp as StartApp
import Task exposing (..)
import Effects exposing (..)
import List exposing (..)
import String exposing (words, join, cons, uncons)
import Char
import Svg as SVG
import Svg.Attributes as SVGA
import Svg.Events as SVGE
import Dict exposing (..)


-- Model
subMenu = []

type alias Model = 
  { currentArea : Maybe Area
  , areas : Dict Int Area
  , desiredWidth : Int
  , vpSize : (Float,Float) 
  }

initWidth = computeDesiredWidth initVpSize

mapRatio : Float
mapRatio = 800/617

initialModel = Model Nothing pts initWidth initVpSize

-- View
view address model =
  div [id "container",computeWMargin model]
      [div [id "mapApp", computeVMargin model] 
           [div [ id "mapContainer"
                , setSize (.desiredWidth model
                          , ((toFloat (.desiredWidth model)) / mapRatio))
                ]
                [ img [src "images/mapPrototype.png"
                      , id "mapPic"
                      ]
                      []
                , (coordsToSVGs address 
                                model
                                (.desiredWidth model)
                   )      
                ]
           , renderSideTab address model
           
           ]]
  
renderSideTab : Signal.Address Action -> Model -> Html
renderSideTab address model = 
  case (.currentArea model) of
    Nothing -> 
      div [ id "sideTab"]
          [ h2 [] [text "Yamana garden explorer"]
          , p  [] [text "Move the cursor over an area to know more about it!"]
          ]
    Just curAr -> 
      div [id "sideTab"]
          [ h2  [] [text (.name curAr)]
          , img [src ("images/thumbs/"++(.picture curAr))]
                []
          , maybeElem (.descr curAr) (\s -> p [] [text s])
          ]

  


type Action = 
    NoOp
  | AreaHover Int
  | Reset
  | Resize (Float,Float)

update action model =
  case action of
    NoOp        -> (model,none)
    Reset       -> (model,none) --{model | currentArea = Nothing}
    AreaHover n -> ({model | currentArea = Dict.get n (.areas model)},none)
    Resize newSize -> ({ model | 
                         vpSize = newSize
                       , desiredWidth = computeDesiredWidth (.vpSize model)
                       },none)


--Main

port vpSizePort : Signal (Float,Float)

vpSizeUpdate : Signal Action
vpSizeUpdate = Signal.map (\v -> Resize v) vpSizePort

port initVpSize : (Float,Float)

app =
    StartApp.start
          { init = (initialModel, none)
          , view = view
          , update = update
          , inputs = [vpSizeUpdate]
          }

main =
    app.html

port tasks : Signal (Task.Task Effects.Never ())
port tasks =
  app.tasks
      
-- Utils

type alias Area = 
  { id : Int
  , points : List Int
  , name : String
  , link : String
  , picture : String
  , descr : String
  }

defArea = Area 0 [] "" "" "" ""

coordsToSVGs : Signal.Address Action -> Model -> Int -> Html
coordsToSVGs addr model dw = 
  let coords' = toScale dw (Dict.values (.areas model))
      id' = case (.currentArea model) of
             Nothing -> 0
             Just curAr -> .id curAr

      poly addr {id, points, name, link, picture, descr} =
       let content =  
        [SVG.polygon [ SVGA.points (String.join "," (List.map toString points))
                     , onMouseOver addr (AreaHover id)
                     , onMouseOut addr Reset
                     , SVGA.fill "blue"
                     , if (id == id') then SVGA.class "isCurrent" else SVGA.class "isNotCurrent"
                     ]
                     [ node "title" [] [SVG.text name]]]
       in if (id == id') then SVG.a [SVGA.xlinkHref link] content else SVG.g [] content  

      wStr = toString dw
      hStr = toString (round (toFloat dw/(1000/771)))          
      

  in SVG.svg [ SVGA.width  wStr
             , SVGA.height hStr
             , SVGA.viewBox ("0 0 " ++ wStr ++ " " ++ hStr)
             ]
             (List.map (poly addr) coords')


toScale : Int -> List Area -> List Area
toScale width xs = 
  let ratio = 1000 / 771
      wScale = 1000 / (toFloat width)
      hScale = 771/(toFloat width/ratio)

      helper xs =
       case xs of
        [] -> []
        (w::h::xs') -> let w' = (toFloat w/wScale)
                           h' = (toFloat h/hScale)
                       in (round w')::(round h')::helper xs'
        (_::[])     -> []
  in List.map (\c -> {c | points = helper (.points c)}) xs    

maybeElem : String -> ( String -> Html ) -> Html
maybeElem s f =
  if String.isEmpty s
  then nullTag
  else f s


nullTag = span [style [("display","none")]] []

--computeMargin : (Float,Float) -> VirtualDom.Property
computeDesiredWidth (vpWidth,vpHeight) = 
  if vpWidth >= 1368
  then 800
  else 600

computeVMargin model =
  let (vpWidth,vpHeight) = .vpSize model
      dh = (toFloat (.desiredWidth model) / mapRatio) + 33
      dw = .desiredWidth model + 33   
  in   
     if vpHeight - dh <= 0 
     then style [("width",(toString (dw + 352)) ++ "px")]
     else style [("margin-top",(toString ((vpHeight - dh)/2)) ++ "px")
                ,("width",(toString (dw + 352)) ++ "px")
                ]  

computeWMargin model =
  let (vpWidth,vpHeight) = .vpSize model
      dw = .desiredWidth model + 385   
  in

  if vpWidth <= 1368
  then style [("background-color","transparent")
             ,("box-shadow","none")
             ,("position","static")
             ,("height","initial")
             ]
  else 
    let w  = (dw+(vpWidth-dw)/4)
        ml = (vpWidth - w) / 2
    in style [ ("width",(toString w) ++ "px")
             , ("margin-left",(toString ml) ++ "px")
             ]

setSize (w,h) = style [ ("width",(toString w) ++ "px")
                      , ("height",(toString h) ++ "px")
                      ]


-- Data
pts : Dict Int Area
pts =
 Dict.fromList (List.map (\v -> (.id v,v))
  
  [ { defArea | 
      id = 1
    , points = [158,519,284,530,275,609,147,594]
    , name = "Greenhouse"
    , picture = "greenhouse.JPG"   
    }
  , { defArea | 
      id = 2
    , points = [212,403,206,456,235,455,261,458,258,433,269,405]
    , name = "Mandala garden"
    , picture = "mandala.JPG"   
    }
  , { defArea | 
      id = 3 
    , points = [735,370,768,351,773,352,787,386,785,411,773,487,773,487,769,489,768,489,741,479,741,479,741,475,735,470,740,446,744,437,748,409,745,396,734,371]
    , name = "Radish field"
    , picture = "radish.JPG"   
    }
  , { defArea | 
      id = 4
    , points = [273,414,279,411,346,413,354,425,351,456,344,462,267,456,263,439,264,424,267,417]
    , name = "Fish pond"
    , picture = "pond.JPG"
    , descr = "The place with all the pretty fish"   
    }
  , { defArea | 
      id = 5
    , points = [663,451,765,494,751,514,743,551,743,573,749,612,749,612,748,622,731,624,722,616,707,599,695,578,676,588,644,529,644,496,663,450]
    , name = "Section B"
    , picture = "bsection.JPG"   
    }
  , { defArea | 
      id = 6
    , points = [359,421,355,436,364,438,364,438,367,420]
    , name = "Shower"
    , picture = "shower.JPG"   
    }
  --, { defArea | 
  --    id = 
  --  , points = []
  --  , name = ""
  --  , picture = ""   
  --  }   
  ])

