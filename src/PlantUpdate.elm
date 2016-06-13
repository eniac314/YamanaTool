module PlantUpdate where

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
import Json.Decode as Json

-- Model
subMenu = []

type alias Model = 
  { desiredWidth : Int
  , vpSize : (Float,Float) 
  , nbrLoc : Int
  , nbrPic : Int
  , listLoc : Locations
  }


initialModel = Model 800 initVpSize 1 0 (Ok [])


-- View
view address model =
  div [id "container",computeWMargin (.vpSize model)]
      [div [id "mapApp", computeVMargin (.vpSize model)] 
           [ Html.form [ id "plantUpdateForm" 
                       , action "/plant_update"
                       , enctype "multipart/form-data"
                       , method "post"
                       ]
                       [ div [ id "names"]
                             [ label [for "plantName"] [text "plant name:"]
                             , input [type' "text", name "plantName"] [] 
                             , label [for "plantNameChinese"] [text "plant name (chinese):"]
                             , input [type' "text", name "plantNameChinese"] []
                             ] 
                       , br [] []
                       , renderLocs address model
                       , br [] []
                       , div [id "usage"]
                             [ label [for "usage"] [text "usage: "]
                             , input [type' "textarea"
                                     , name "usage"
                                     , value ""] []
                             ]
                       , br [] []
                       , div [id "remarks"]
                             [ label [for "remarks"] [text "remarks: "]
                             , input [type' "textarea"
                                     , name "remarks"
                                     , value ""] []
                             ]
                       , br [] []
                       , renderPics address model
                       , br [] []
                       , div [] [input [type' "submit", value "Upload"] []]
                       , input [ type' "hidden"
                               , name "nbrLoc"
                               , value (toString (.nbrLoc model))
                               ] []
                       , input [ type' "hidden"
                               , name "nbrPic"
                               , value (toString (.nbrPic model))
                               ] []
                       ]
           ]
      ]

renderLocs address model = 
  let renderLoc n =
        
            [ label [for ("loc"++toString n)]
                    [text ("location " ++ (toString n) ++ ": ")]
            , select [ name ("loc"++toString n), id ("loc"++toString n)]
                     (options model)
            
            , label [ id "dateLbl"]
                    [ span [] [text "date: "]
                    , input [ type' "date"
                            , id "dateInput"
                            , name ("date"++toString n)]
                            []
                    ]
            , br [] []
            ]
      
      go n = 
        if n == 0
        then []
        else (renderLoc n) :: go (n-1)

  in div [id "locsAvail"]
         ( (go (.nbrLoc model)
           |> List.reverse
           |> List.concat) ++
          [ br [] []
          , button [onClick address AddLoc, type' "button"]
                   [text "add one"]
          , button [onClick address RemoveLoc, type' "button"]
                   [text "remove one"]
          ]
         )  

options model = 
  case .listLoc model of 
    Err _ -> []
    Ok xs -> List.map (\s -> option [value s ] [text s]) xs

renderPics address model =
  let renderPic n = 
          input [type' "file", name ("file" ++ toString n)] []
      
      go n = 
        if n == 0
        then []
        else (renderPic n) :: go (n-1)   
  
  in div [id "picsInput"]
         (([ label [for "mainPicture"] [text "main picture: "]
           , input [type' "file", name "mainPicture"] []
           , br [] []
           , text "complementary pictures: (5 max)"
           ]
         ++ (go (.nbrPic model))) ++
         [ br [] []
         , button [onClick address AddPic, type' "button"]
                   [text "add one"]
         , button [onClick address RemovePic, type' "button"]
                   [text "remove one"]
         ])

type alias Locations = Result Http.Error (List String) 

type Action = 
    NoOp
  | Resize (Float,Float)
  | AddLoc
  | RemoveLoc
  | AddPic
  | RemovePic
  | RequestLocations
  | UpdateLocations Locations

update action model =
  case action of
    NoOp        -> (model,none)
    Resize newSize -> ({model | vpSize = newSize},none)
    AddLoc -> ({ model | 
                nbrLoc = if (.nbrLoc model) < 20
                         then (.nbrLoc model) + 1
                         else (.nbrLoc model)
               }
              , none)
    RemoveLoc -> ({ model | 
                    nbrLoc = if (.nbrLoc model) > 0
                             then (.nbrLoc model) - 1
                             else (.nbrLoc model)
                   }
                  , none)
    AddPic -> ({ model | 
                 nbrPic = if (.nbrPic model) < 5
                          then (.nbrPic model) + 1
                          else (.nbrPic model)
               }
              , none)

    RemovePic -> ({ model | 
                    nbrPic = if (.nbrPic model) > 0
                             then (.nbrPic model) - 1
                             else (.nbrPic model)
                  }
                 , none)
    RequestLocations -> (model,requestLocations)
    UpdateLocations l -> ({model | listLoc = l}, none)

requestLocations = 
  Http.get locationsDecoder "/locations"
    |> Task.toResult
    |> Task.map UpdateLocations
    |> Effects.task

locationsDecoder : Json.Decoder (List String)
locationsDecoder = Json.list Json.string

--Main

port vpSizePort : Signal (Float,Float)

vpSizeUpdate : Signal Action
vpSizeUpdate = Signal.map (\v -> Resize v) vpSizePort

port initVpSize : (Float,Float)

app =
    StartApp.start
          { init = (initialModel, requestLocations)
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


