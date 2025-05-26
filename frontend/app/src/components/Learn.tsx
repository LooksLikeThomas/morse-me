import React from "react";
import image from "../images/morse-cheatsheet.png";

export default function Learn () {
    return (
        <React.Fragment>
            <img src={image} alt={"Morse-Cheatsheet"} className={"h-[400px]"}/>
        </React.Fragment>
    )
}