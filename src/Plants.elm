module Plants where

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
import Http as Http
import Json.Decode as Json exposing (..)
import Date exposing (..)



-- Model
subMenu = []

type alias Model = 
  { desiredWidth : Int
  , vpSize : (Float,Float)
  , content : Content
  }


type alias Content = Result Http.Error (List Plant) 

type alias Plant = 
  { name : (String,String)
  , availability : List (Location,Date) 
  , usage : (String,String)
  , remarks : (String,String)
  , pics : List Picture
  }

defPlant = Plant ("defPlant","") [] ("","") ("","") [] 

type alias Location = String
type alias Picture  = String

initialModel = Model 800 initVpSize (Ok [defPlant])


-- View
view address model =
  div [id "container",computeWMargin (.vpSize model)]
      [div [id "mapApp", computeVMargin (.vpSize model)] 
           [ text (toString (.content model))
           ]
      ]
  
type Action = 
    NoOp
  | Resize (Float,Float)
  | RequestContent
  | UpdateContent Content


-- Update

update action model =
  case action of
    NoOp        -> (model,none)
    Resize newSize -> ({model | vpSize = newSize},none)
    RequestContent -> (model,requestContent)
    UpdateContent c -> ({model | content = c },none)


--tmpy c = 
--  case c of 
--   Err e -> "Error"
--   Ok c' -> 
--    let d = snd (Maybe.withDefault ("def",toDate "fed") (List.head (.availability c')))
--    in (day' d)
--       ++ " " ++
--       (months' d)
--       ++ " " ++
--       (year' d)

months' date = 
  case Date.month date of
    Jan -> "01" 
    Feb -> "02"
    Mar -> "03"
    Apr -> "04"
    May -> "05"
    Jun -> "06"
    Jul -> "07"
    Aug -> "08"
    Sep -> "09"
    Oct -> "10"
    Nov -> "11"
    Dec -> "12"

day' date  = 
  let res = toString (Date.day date)
  in if  String.length res == 1
     then "0"++res
     else res
     
year' date = toString (Date.year date)


-- Http

requestContent = 
  Http.get (Json.list plantDecoder) "/plants_json"
    |> Task.toResult
    |> Task.map UpdateContent
    |> Effects.task


plantDecoder : Json.Decoder Plant
plantDecoder = 
  Json.object5 
    Plant
    ("name" := Json.tuple2 (,) Json.string Json.string)
    ("availability" := Json.list
                        (Json.tuple2 
                          (\l t -> (l,toDate t))
                          Json.string
                          Json.string
                        )
    )
    ("usage" := Json.tuple2 (,) Json.string Json.string)
    ("remarks" := Json.tuple2 (,) Json.string Json.string)
    ("pics" := Json.list Json.string)



toDate : String -> Date
toDate t = Result.withDefault
               (Date.fromTime 0)
               (Date.fromString t)

--Main

port vpSizePort : Signal (Float,Float)

vpSizeUpdate : Signal Action
vpSizeUpdate = Signal.map (\v -> Resize v) vpSizePort

port initVpSize : (Float,Float)

app =
    StartApp.start
          { init = (initialModel, requestContent)
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
  if vpWidth - 1368 <= 0 
  then style [("background-color","transparent")
             ,("box-shadow","none")
             ,("position","static")
             ]
  else 
    let w  = (1185+(vpWidth-1185)/4)
        ml = (vpWidth - w) / 2
    in style [ ("width",(toString w) ++ "px")
             , ("margin-left",(toString ml) ++ "px")
             ]


-- Data


