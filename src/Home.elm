module Home where

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
  { desiredWidth : Int
  , vpSize : (Float,Float) 
  }


initialModel = Model 800 initVpSize


-- View
view address model =
  div [id "container",computeWMargin (.vpSize model)]
      [div [id "mapApp", computeVMargin (.vpSize model)] 
           [ div [ class "picContainer"]
                 [ a [ href "/map"]
                     [ img [ src "/images/map.png"]
                           []
                     , p [] [ text "Map explorer"]
                     ]
                 ]
           , div [ class "picContainer"]
                 [ a [ href "/plants"]
                     [ img [ src "/images/plants.JPG"]
                           []
                     , p [] [ text "Plant database"]
                     ]
                 ]
           ]
      ]
  
type Action = 
    NoOp
  | Resize (Float,Float)

update action model =
  case action of
    NoOp        -> (model,none)
    Resize newSize -> ({model | vpSize = newSize},none)


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



maybeElem : String -> ( String -> Html ) -> Html
maybeElem s f =
  if String.isEmpty s
  then nullTag
  else f s


nullTag = span [style [("display","none")]] []

--computeMargin : (Float,Float) -> VirtualDom.Property
computeVMargin (vpWidth,vpHeight) =
  if vpHeight - 650 <= 0 
  then style []
  else style [("margin-top",(toString ((vpHeight - 650)/2)) ++ "px")]  

computeWMargin (vpWidth,vpHeight) =
  if vpWidth - 1200 <= 0 
  then style [("background-color","transparent")
             ,("box-shadow","none")
             ]
  else 
    let w  = (1185+(vpWidth-1185)/4)
        ml = (vpWidth - w) / 2
    in style [ ("width",(toString w) ++ "px")
             , ("margin-left",(toString ml) ++ "px")
             ]


-- Data


